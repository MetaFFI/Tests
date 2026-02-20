package call_java

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"reflect"
	"runtime"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/MetaFFI/sdk/idl_entities/go/IDL"
)

// ---------------------------------------------------------------------------
// Benchmark configuration (from env or defaults)
// ---------------------------------------------------------------------------

func getIntEnv(key string, defaultVal int) int {
	v := os.Getenv(key)
	if v == "" {
		return defaultVal
	}
	var n int
	_, err := fmt.Sscanf(v, "%d", &n)
	if err != nil {
		return defaultVal
	}
	return n
}

func parseScenarioFilter() map[string]struct{} {
	raw := strings.TrimSpace(os.Getenv("METAFFI_TEST_SCENARIOS"))
	if raw == "" {
		return nil
	}

	res := make(map[string]struct{})
	for _, part := range strings.Split(raw, ",") {
		k := strings.TrimSpace(part)
		if k != "" {
			res[k] = struct{}{}
		}
	}
	if len(res) == 0 {
		return nil
	}
	return res
}

func scenarioFilterKey(name string, dataSize *int) string {
	if dataSize == nil {
		return name
	}
	return fmt.Sprintf("%s_%d", name, *dataSize)
}

func shouldRunScenario(filter map[string]struct{}, name string, dataSize *int) bool {
	if len(filter) == 0 {
		return true
	}
	_, ok := filter[scenarioFilterKey(name, dataSize)]
	return ok
}

// ---------------------------------------------------------------------------
// Statistics helpers
// ---------------------------------------------------------------------------

type PhaseStats struct {
	MeanNs   float64    `json:"mean_ns"`
	MedianNs float64    `json:"median_ns"`
	P95Ns    float64    `json:"p95_ns"`
	P99Ns    float64    `json:"p99_ns"`
	StddevNs float64    `json:"stddev_ns"`
	CI95Ns   [2]float64 `json:"ci95_ns"`
}

type BenchmarkResult struct {
	Scenario        string                `json:"scenario"`
	DataSize        *int                  `json:"data_size"`
	Status          string                `json:"status"`
	RawIterationsNs []int64               `json:"raw_iterations_ns"`
	Phases          map[string]PhaseStats `json:"phases"`
}

type ResultFile struct {
	Metadata    Metadata          `json:"metadata"`
	Correctness interface{}       `json:"correctness"`
	Init        InitTiming        `json:"initialization"`
	Benchmarks  []BenchmarkResult `json:"benchmarks"`
}

type Metadata struct {
	Host        string      `json:"host"`
	Guest       string      `json:"guest"`
	Mechanism   string      `json:"mechanism"`
	Timestamp   string      `json:"timestamp"`
	Environment Environment `json:"environment"`
	Config      Config      `json:"config"`
}

type Environment struct {
	OS        string `json:"os"`
	Arch      string `json:"arch"`
	GoVersion string `json:"go_version"`
}

type Config struct {
	WarmupIterations   int   `json:"warmup_iterations"`
	MeasuredIterations int   `json:"measured_iterations"`
	BatchMinElapsedNs  int64 `json:"batch_min_elapsed_ns"`
	BatchMaxCalls      int   `json:"batch_max_calls"`
	TimerOverheadNs    int64 `json:"timer_overhead_ns"`
}

type InitTiming struct {
	LoadRuntimePluginNs int64 `json:"load_runtime_plugin_ns"`
	LoadModuleNs        int64 `json:"load_module_ns"`
}

func computeStats(sorted []int64) PhaseStats {
	n := len(sorted)
	if n == 0 {
		return PhaseStats{}
	}

	var sum float64
	for _, v := range sorted {
		sum += float64(v)
	}
	mean := sum / float64(n)

	var median float64
	if n%2 == 0 {
		median = float64(sorted[n/2-1]+sorted[n/2]) / 2.0
	} else {
		median = float64(sorted[n/2])
	}

	p95 := float64(sorted[int(float64(n)*0.95)])
	p99 := float64(sorted[int(math.Min(float64(n)*0.99, float64(n-1)))])

	var sqDiffSum float64
	for _, v := range sorted {
		diff := float64(v) - mean
		sqDiffSum += diff * diff
	}
	stddev := math.Sqrt(sqDiffSum / float64(n))

	se := stddev / math.Sqrt(float64(n))

	return PhaseStats{
		MeanNs:   mean,
		MedianNs: median,
		P95Ns:    p95,
		P99Ns:    p99,
		StddevNs: stddev,
		CI95Ns:   [2]float64{mean - 1.96*se, mean + 1.96*se},
	}
}

func removeOutliersIQR(sorted []int64) []int64 {
	n := len(sorted)
	if n < 4 {
		return sorted
	}

	q1 := float64(sorted[n/4])
	q3 := float64(sorted[3*n/4])
	iqr := q3 - q1
	lower := q1 - 1.5*iqr
	upper := q3 + 1.5*iqr

	result := make([]int64, 0, n)
	for _, v := range sorted {
		if float64(v) >= lower && float64(v) <= upper {
			result = append(result, v)
		}
	}
	return result
}

func measureTimerOverhead() int64 {
	const n = 10000
	samples := make([]int64, n)
	for i := 0; i < n; i++ {
		start := time.Now()
		elapsed := time.Since(start)
		samples[i] = elapsed.Nanoseconds()
	}
	sort.Slice(samples, func(i, j int) bool { return samples[i] < samples[j] })
	return samples[n/2]
}

// ---------------------------------------------------------------------------
// Benchmark runner
// ---------------------------------------------------------------------------

func runBenchmark(
	t *testing.T,
	scenario string,
	dataSize *int,
	warmup int,
	iterations int,
	batchMinElapsedNs int64,
	batchMaxCalls int,
	benchFn func() error,
) BenchmarkResult {
	t.Helper()

	// Warmup
	for i := 0; i < warmup; i++ {
		if err := benchFn(); err != nil {
			t.Fatalf("benchmark %q warmup iteration %d: %v", scenario, i, err)
			return BenchmarkResult{Scenario: scenario, DataSize: dataSize, Status: "FAIL"}
		}
	}

	// Measurement
	rawNs := make([]int64, iterations)
	for i := 0; i < iterations; i++ {
		start := time.Now()
		calls := 0
		for {
			err := benchFn()
			if err != nil {
				t.Fatalf("benchmark %q iteration %d: %v (BENCHMARK INVALIDATED)", scenario, i, err)
				return BenchmarkResult{Scenario: scenario, DataSize: dataSize, Status: "FAIL"}
			}
			calls++
			elapsed := time.Since(start).Nanoseconds()
			if elapsed >= batchMinElapsedNs || calls >= batchMaxCalls {
				perCall := float64(elapsed) / float64(calls)
				if perCall > 0.0 && perCall < 1.0 {
					rawNs[i] = 1
				} else {
					rawNs[i] = int64(math.Round(perCall))
				}
				break
			}
		}
	}

	sortedNs := make([]int64, len(rawNs))
	copy(sortedNs, rawNs)
	sort.Slice(sortedNs, func(i, j int) bool { return sortedNs[i] < sortedNs[j] })

	cleaned := removeOutliersIQR(sortedNs)
	totalStats := computeStats(cleaned)

	return BenchmarkResult{
		Scenario:        scenario,
		DataSize:        dataSize,
		Status:          "PASS",
		RawIterationsNs: rawNs,
		Phases: map[string]PhaseStats{
			"total": totalStats,
		},
	}
}

// ---------------------------------------------------------------------------
// Benchmark tests (7 scenarios)
// ---------------------------------------------------------------------------

func TestBenchmarkAll(t *testing.T) {
	mode := os.Getenv("METAFFI_TEST_MODE")
	if mode == "correctness" {
		t.Skip("Skipping benchmarks: METAFFI_TEST_MODE=correctness")
	}

	warmup := getIntEnv("METAFFI_TEST_WARMUP", 100)
	iterations := getIntEnv("METAFFI_TEST_ITERATIONS", 10000)
	batchMinElapsedNs := int64(getIntEnv("METAFFI_TEST_BATCH_MIN_ELAPSED_NS", 10000))
	batchMaxCalls := getIntEnv("METAFFI_TEST_BATCH_MAX_CALLS", 100000)
	scenarioFilter := parseScenarioFilter()

	timerOverhead := measureTimerOverhead()
	t.Logf("Timer overhead: %d ns", timerOverhead)
	if len(scenarioFilter) > 0 {
		t.Logf("Scenario filter enabled: %s", os.Getenv("METAFFI_TEST_SCENARIOS"))
	}

	var benchmarks []BenchmarkResult

	// saveProgress writes all results collected so far to disk.
	// If a later scenario crashes the process (e.g. JVM EXCEPTION_ACCESS_VIOLATION),
	// results from earlier scenarios are already persisted.
	saveProgress := func() {
		if len(benchmarks) > 0 {
			writeResults(t, benchmarks, timerOverhead, warmup, iterations, batchMinElapsedNs, batchMaxCalls)
		}
	}

	// --- Scenario 1: Void call ---
	if shouldRunScenario(scenarioFilter, "void_call", nil) {
		t.Run("void_call", func(t *testing.T) {
			ff := load(t, "class=guest.CoreFunctions,callable=noOp",
				nil, nil)

			result := runBenchmark(t, "void_call", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				_, err := ff()
				return err
			})
			benchmarks = append(benchmarks, result)
			saveProgress()
		})
	}

	// --- Scenario 2: Primitive echo (divIntegers) ---
	if shouldRunScenario(scenarioFilter, "primitive_echo", nil) {
		t.Run("primitive_echo", func(t *testing.T) {
			ff := load(t, "class=guest.CoreFunctions,callable=divIntegers",
				[]IDL.MetaFFITypeInfo{ti(IDL.INT64), ti(IDL.INT64)},
				[]IDL.MetaFFITypeInfo{ti(IDL.FLOAT64)})

			result := runBenchmark(t, "primitive_echo", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				ret, err := ff(int64(10), int64(2))
				if err != nil {
					return err
				}
				v, ok := ret[0].(float64)
				if !ok || math.Abs(v-5.0) > 1e-10 {
					return fmt.Errorf("divIntegers(10,2): got %v, want 5.0", ret[0])
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
			saveProgress()
		})
	}

	// --- Scenario 3: String echo ---
	if shouldRunScenario(scenarioFilter, "string_echo", nil) {
		t.Run("string_echo", func(t *testing.T) {
			ff := load(t, "class=guest.CoreFunctions,callable=joinStrings",
				[]IDL.MetaFFITypeInfo{tiArray(IDL.STRING8_ARRAY, 1)},
				[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

			result := runBenchmark(t, "string_echo", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				ret, err := ff([]string{"hello", "world"})
				if err != nil {
					return err
				}
				if v, ok := ret[0].(string); !ok || v != "hello,world" {
					return fmt.Errorf("joinStrings: got %v, want \"hello,world\"", ret[0])
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
			saveProgress()
		})
	}

	// --- Scenario 4: Array sum (varying sizes, packed 1D int[]) ---
	for _, size := range []int{10, 100, 1000, 10000} {
		size := size
		if !shouldRunScenario(scenarioFilter, "array_sum", &size) {
			continue
		}
		t.Run(fmt.Sprintf("array_sum_%d", size), func(t *testing.T) {
			ff := load(t, "class=guest.ArrayFunctions,callable=sumInt1dArray",
				[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_PACKED_ARRAY, 1)},
				[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

			row := make([]int32, size)
			var expectedSum int32
			for i := 0; i < size; i++ {
				row[i] = int32(i + 1)
				expectedSum += int32(i + 1)
			}

			sizePtr := size
			result := runBenchmark(t, "array_sum", &sizePtr, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				ret, err := ff(row)
				if err != nil {
					return err
				}
				if v, ok := ret[0].(int32); !ok || v != expectedSum {
					return fmt.Errorf("sumInt1dArray: got %v, want %d", ret[0], expectedSum)
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
			saveProgress()
		})
	}

	// --- Scenario: Callback invocation (before any_echo to avoid Go→Java heap corruption) ---
	if shouldRunScenario(scenarioFilter, "callback", nil) {
		t.Run("callback", func(t *testing.T) {
			runtime.LockOSThread()
			defer runtime.UnlockOSThread()

			adapter := load(t, "class=metaffi.api.accessor.CallbackAdapters,callable=asInterface",
				[]IDL.MetaFFITypeInfo{ti(IDL.CALLABLE), ti(IDL.STRING8)},
				[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})

			ff := load(t, "class=guest.CoreFunctions,callable=callCallbackAdd",
				[]IDL.MetaFFITypeInfo{tiAlias(IDL.HANDLE, "java.util.function.IntBinaryOperator")},
				[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

			adder := func(a, b int32) int32 { return a + b }
			adapterRet := call(t, "CallbackAdapters.asInterface", adapter, adder, "java.util.function.IntBinaryOperator")
			if adapterRet[0] == nil {
				t.Fatal("CallbackAdapters.asInterface: got nil proxy")
			}
			proxy := adapterRet[0]

			result := runBenchmark(t, "callback", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				ret, err := ff(proxy)
				if err != nil {
					return err
				}
				if v, ok := ret[0].(int32); !ok || v != 3 {
					return fmt.Errorf("callCallbackAdd: got %v, want 3", ret[0])
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
			saveProgress()
			// Keep callback/proxy reachable for the entire benchmark run.
			// Without this, long runs can trigger GC and crash in callback dispatch.
			runtime.KeepAlive(adder)
			runtime.KeepAlive(proxy)
		})
	}

	// --- Scenario: Dynamic any echo (mixed array payload) ---
	// NOTE: any_echo with large payloads can corrupt CDT heap state in Go→Java,
	// causing subsequent scenarios to crash. Placed after callback intentionally.
	{
		anyEchoSize := 100
		if shouldRunScenario(scenarioFilter, "any_echo", &anyEchoSize) {
			t.Run("any_echo_100", func(t *testing.T) {
				ff := load(t, "class=guest.CoreFunctions,callable=echoAny",
					[]IDL.MetaFFITypeInfo{ti(IDL.ANY)},
					[]IDL.MetaFFITypeInfo{ti(IDL.ANY)})

				pattern := []any{int32(1), "two", float64(3.0)}
				payload := make([]any, anyEchoSize)
				for i := 0; i < anyEchoSize; i++ {
					payload[i] = pattern[i%len(pattern)]
				}

				sizePtr := anyEchoSize
				result := runBenchmark(t, "any_echo", &sizePtr, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
					ret, err := ff(payload)
					if err != nil {
						return err
					}
					if len(ret) == 0 || ret[0] == nil {
						return fmt.Errorf("echoAny: got empty/nil return")
					}
					v := reflect.ValueOf(ret[0])
					if v.Kind() != reflect.Slice && v.Kind() != reflect.Array {
						return fmt.Errorf("echoAny: unexpected return type %T", ret[0])
					}
					if v.Len() != anyEchoSize {
						return fmt.Errorf("echoAny: got len %d, want %d", v.Len(), anyEchoSize)
					}
					return nil
				})
				benchmarks = append(benchmarks, result)
				saveProgress()
			})
		}
	}

	// --- Scenario: Object create + method call ---
	if shouldRunScenario(scenarioFilter, "object_method", nil) {
		t.Run("object_method", func(t *testing.T) {
			newEntity := load(t, "class=guest.SomeClass,callable=<init>",
				[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)},
				[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)})

			printEntity := load(t, "class=guest.SomeClass,callable=print,instance_required",
				[]IDL.MetaFFITypeInfo{ti(IDL.HANDLE)},
				[]IDL.MetaFFITypeInfo{ti(IDL.STRING8)})

			result := runBenchmark(t, "object_method", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				// Create instance
				instanceRet, err := newEntity("bench")
				if err != nil {
					return fmt.Errorf("<init>: %w", err)
				}
				instance := instanceRet[0]

				// Call method
				printRet, err := printEntity(instance)
				if err != nil {
					return fmt.Errorf("print: %w", err)
				}
				if v, ok := printRet[0].(string); !ok || v != "Hello from SomeClass bench" {
					return fmt.Errorf("print: got %v, want \"Hello from SomeClass bench\"", printRet[0])
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
			saveProgress()
		})
	}

	// --- Scenario: Error propagation ---
	if shouldRunScenario(scenarioFilter, "error_propagation", nil) {
		t.Run("error_propagation", func(t *testing.T) {
			ff := load(t, "class=guest.CoreFunctions,callable=returnsAnError", nil, nil)

			result := runBenchmark(t, "error_propagation", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				_, err := ff()
				if err == nil {
					return fmt.Errorf("expected error but got nil")
				}
				// Error IS expected -- this is the successful path
				return nil
			})
			benchmarks = append(benchmarks, result)
			saveProgress()
		})
	}

	if len(benchmarks) == 0 {
		t.Fatalf("METAFFI_TEST_SCENARIOS selected no benchmark scenarios: %q", os.Getenv("METAFFI_TEST_SCENARIOS"))
	}

	// --- Write results to JSON ---
	writeResults(t, benchmarks, timerOverhead, warmup, iterations, batchMinElapsedNs, batchMaxCalls)

	// Benchmark scenarios can leave the JVM/plugin in unstable state for
	// subsequent correctness tests in the same package run. Refresh runtime/module.
	if err := reloadRuntimeModule(); err != nil {
		t.Fatalf("failed to reload runtime after benchmarks: %v", err)
	}
}

func writeResults(
	t *testing.T,
	benchmarks []BenchmarkResult,
	timerOverhead int64,
	warmup, iterations int,
	batchMinElapsedNs int64,
	batchMaxCalls int,
) {
	t.Helper()

	resultPath := os.Getenv("METAFFI_TEST_RESULTS_FILE")
	if resultPath == "" {
		resultPath = "../../results/go_to_java_metaffi.json"
	}

	result := ResultFile{
		Metadata: Metadata{
			Host:      "go",
			Guest:     "java",
			Mechanism: "metaffi",
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			Environment: Environment{
				OS:        runtime.GOOS,
				Arch:      runtime.GOARCH,
				GoVersion: runtime.Version(),
			},
			Config: Config{
				WarmupIterations:   warmup,
				MeasuredIterations: iterations,
				BatchMinElapsedNs:  batchMinElapsedNs,
				BatchMaxCalls:      batchMaxCalls,
				TimerOverheadNs:    timerOverhead,
			},
		},
		Benchmarks: benchmarks,
	}

	data, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		t.Fatalf("Failed to marshal results to JSON: %v", err)
	}

	if err := os.WriteFile(resultPath, data, 0644); err != nil {
		t.Logf("WARNING: Failed to write results to %s: %v", resultPath, err)
	} else {
		t.Logf("Results written to %s", resultPath)
	}
}
