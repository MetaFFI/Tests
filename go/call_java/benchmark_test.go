package call_java

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"runtime"
	"sort"
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

	timerOverhead := measureTimerOverhead()
	t.Logf("Timer overhead: %d ns", timerOverhead)

	var benchmarks []BenchmarkResult

	// --- Scenario 1: Void call ---
	t.Run("void_call", func(t *testing.T) {
		ff := load(t, "class=guest.CoreFunctions,callable=waitABit",
			[]IDL.MetaFFITypeInfo{ti(IDL.INT64)}, nil)

		result := runBenchmark(t, "void_call", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
			_, err := ff(int64(0))
			return err
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 2: Primitive echo (divIntegers) ---
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
	})

	// --- Scenario 3: String echo ---
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
	})

	// --- Scenario 4: Array sum (varying sizes) ---
	// Java uses int[], so use sumRaggedArray with a single-row ragged array
	for _, size := range []int{10, 100, 1000, 10000} {
		size := size
		t.Run(fmt.Sprintf("array_sum_%d", size), func(t *testing.T) {
			ff := load(t, "class=guest.ArrayFunctions,callable=sumRaggedArray",
				[]IDL.MetaFFITypeInfo{tiArray(IDL.INT32_ARRAY, 2)},
				[]IDL.MetaFFITypeInfo{ti(IDL.INT32)})

			// Build array: single row of `size` elements [1, 2, ..., size]
			row := make([]int32, size)
			var expectedSum int32
			for i := 0; i < size; i++ {
				row[i] = int32(i + 1)
				expectedSum += int32(i + 1)
			}
			arr := [][]int32{row}

			sizePtr := size
			result := runBenchmark(t, "array_sum", &sizePtr, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				ret, err := ff(arr)
				if err != nil {
					return err
				}
				if v, ok := ret[0].(int32); !ok || v != expectedSum {
					return fmt.Errorf("sumRaggedArray: got %v, want %d", ret[0], expectedSum)
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 5: Callback invocation ---
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
		// Keep callback/proxy reachable for the entire benchmark run.
		// Without this, long runs can trigger GC and crash in callback dispatch.
		runtime.KeepAlive(adder)
		runtime.KeepAlive(proxy)
	})

	// --- Scenario 6: Object create + method call ---
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
	})

	// --- Scenario 7: Error propagation ---
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
	})

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
