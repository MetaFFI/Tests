package call_java_jni

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"testing"
	"time"
)

// ---------------------------------------------------------------------------
// Global state set by TestMain
// ---------------------------------------------------------------------------

var (
	jvmInitNs    int64
	classLoadNs  int64
)

func TestMain(m *testing.M) {
	runtime.LockOSThread()

	srcRoot := os.Getenv("METAFFI_SOURCE_ROOT")
	if srcRoot == "" {
		fmt.Fprintln(os.Stderr, "FATAL: METAFFI_SOURCE_ROOT must be set")
		os.Exit(1)
	}

	jarPath := filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "java", "test_bin", "guest_java.jar")

	// --- Initialize JVM ---
	initStart := time.Now()
	if err := JVMInitialize(jarPath); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}
	jvmInitNs = time.Since(initStart).Nanoseconds()

	// --- Load classes ---
	loadStart := time.Now()
	if err := JNILoadClasses(); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}

	// Also initialize callback helper
	if err := InitCallbackHelper(); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}
	classLoadNs = time.Since(loadStart).Nanoseconds()

	fmt.Fprintf(os.Stderr, "JVM init: %d ms, class load: %d ms\n",
		jvmInitNs/1e6, classLoadNs/1e6)

	code := m.Run()

	JVMDestroy()
	os.Exit(code)
}

// ---------------------------------------------------------------------------
// Benchmark configuration
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
// Statistics helpers (same schema as other benchmarks)
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
	TimerOverheadNs    int64 `json:"timer_overhead_ns"`
}

type InitTiming struct {
	JVMInitNs   int64 `json:"jvm_init_ns"`
	ClassLoadNs int64 `json:"class_load_ns"`
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
	benchFn func() error,
) BenchmarkResult {
	t.Helper()

	for i := 0; i < warmup; i++ {
		if err := benchFn(); err != nil {
			t.Fatalf("benchmark %q warmup iteration %d: %v", scenario, i, err)
			return BenchmarkResult{Scenario: scenario, DataSize: dataSize, Status: "FAIL"}
		}
	}

	rawNs := make([]int64, iterations)
	for i := 0; i < iterations; i++ {
		start := time.Now()
		err := benchFn()
		elapsed := time.Since(start).Nanoseconds()

		if err != nil {
			t.Fatalf("benchmark %q iteration %d: %v (BENCHMARK INVALIDATED)", scenario, i, err)
			return BenchmarkResult{Scenario: scenario, DataSize: dataSize, Status: "FAIL"}
		}
		rawNs[i] = elapsed
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

	timerOverhead := measureTimerOverhead()
	t.Logf("Timer overhead: %d ns", timerOverhead)

	var benchmarks []BenchmarkResult

	// --- Scenario 1: Void call ---
	t.Run("void_call", func(t *testing.T) {
		result := runBenchmark(t, "void_call", nil, warmup, iterations, func() error {
			return BenchVoidCall()
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 2: Primitive echo ---
	t.Run("primitive_echo", func(t *testing.T) {
		result := runBenchmark(t, "primitive_echo", nil, warmup, iterations, func() error {
			v, err := BenchPrimitiveEcho()
			if err != nil {
				return err
			}
			if math.Abs(v-5.0) > 1e-10 {
				return fmt.Errorf("divIntegers: got %v, want 5.0", v)
			}
			return nil
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 3: String echo ---
	t.Run("string_echo", func(t *testing.T) {
		result := runBenchmark(t, "string_echo", nil, warmup, iterations, func() error {
			v, err := BenchStringEcho()
			if err != nil {
				return err
			}
			if v != "hello,world" {
				return fmt.Errorf("joinStrings: got %q, want \"hello,world\"", v)
			}
			return nil
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 4: Array sum (varying sizes) ---
	for _, size := range []int{10, 100, 1000, 10000} {
		size := size

		// Compute expected sum
		expectedSum := 0
		for i := 1; i <= size; i++ {
			expectedSum += i
		}

		t.Run(fmt.Sprintf("array_sum_%d", size), func(t *testing.T) {
			sizePtr := size
			result := runBenchmark(t, "array_sum", &sizePtr, warmup, iterations, func() error {
				v, err := BenchArraySum(size)
				if err != nil {
					return err
				}
				if v != expectedSum {
					return fmt.Errorf("sumRaggedArray: got %d, want %d", v, expectedSum)
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 5: Object create + method call ---
	t.Run("object_method", func(t *testing.T) {
		result := runBenchmark(t, "object_method", nil, warmup, iterations, func() error {
			v, err := BenchObjectMethod()
			if err != nil {
				return err
			}
			if v != "Hello from SomeClass bench" {
				return fmt.Errorf("print: got %q, want \"Hello from SomeClass bench\"", v)
			}
			return nil
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 6: Callback ---
	t.Run("callback", func(t *testing.T) {
		result := runBenchmark(t, "callback", nil, warmup, iterations, func() error {
			v, err := BenchCallback()
			if err != nil {
				return err
			}
			if v != 3 {
				return fmt.Errorf("callCallbackAdd: got %d, want 3", v)
			}
			return nil
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 7: Error propagation ---
	t.Run("error_propagation", func(t *testing.T) {
		result := runBenchmark(t, "error_propagation", nil, warmup, iterations, func() error {
			return BenchErrorPropagation()
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Write results ---
	writeResults(t, benchmarks, timerOverhead, warmup, iterations)
}

// ---------------------------------------------------------------------------
// JSON output
// ---------------------------------------------------------------------------

func writeResults(t *testing.T, benchmarks []BenchmarkResult, timerOverhead int64, warmup, iterations int) {
	t.Helper()

	resultPath := os.Getenv("METAFFI_TEST_RESULTS_FILE")
	if resultPath == "" {
		resultPath = filepath.Join("..", "..", "..", "results", "go_to_java_jni.json")
	}

	result := ResultFile{
		Metadata: Metadata{
			Host:      "go",
			Guest:     "java",
			Mechanism: "jni",
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			Environment: Environment{
				OS:        runtime.GOOS,
				Arch:      runtime.GOARCH,
				GoVersion: runtime.Version(),
			},
			Config: Config{
				WarmupIterations:   warmup,
				MeasuredIterations: iterations,
				TimerOverheadNs:    timerOverhead,
			},
		},
		Init: InitTiming{
			JVMInitNs:   jvmInitNs,
			ClassLoadNs: classLoadNs,
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
