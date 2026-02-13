package call_python3_cpython

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
// Global state (loaded once in TestMain)
// ---------------------------------------------------------------------------

var (
	pyMod            pyObj
	waitABitFunc     pyObj
	divIntegersFunc  pyObj
	joinStringsFunc  pyObj
	acceptsRaggedFn  pyObj
	someClassObj     pyObj
	callCallbackFn   pyObj
	returnsAnErrFn   pyObj
	pythonVersionStr string

	// Init timing (reported separately)
	pyInitNs     int64
	moduleLoadNs int64
)

// ---------------------------------------------------------------------------
// TestMain -- initialize CPython, load modules, run tests, finalize
// ---------------------------------------------------------------------------

func TestMain(m *testing.M) {
	// Pin goroutine to OS thread -- CPython's GIL requires consistent thread identity
	runtime.LockOSThread()

	srcRoot := os.Getenv("METAFFI_SOURCE_ROOT")
	if srcRoot == "" {
		fmt.Fprintln(os.Stderr, "FATAL: METAFFI_SOURCE_ROOT must be set")
		os.Exit(1)
	}

	// Python module parent directory (contains "module/" package)
	modulePath := filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "python3")

	// --- Phase 1: Initialize Python runtime ---
	start := time.Now()
	if err := PyInitialize(modulePath); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}
	pyInitNs = time.Since(start).Nanoseconds()

	// --- Phase 2: Import module and load function references ---
	start = time.Now()

	var err error
	pyMod, err = PyImportModule("module")
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: %v\n", err)
		os.Exit(1)
	}

	waitABitFunc = mustAttr("wait_a_bit")
	divIntegersFunc = mustAttr("div_integers")
	joinStringsFunc = mustAttr("join_strings")
	acceptsRaggedFn = mustAttr("accepts_ragged_array")
	someClassObj = mustAttr("SomeClass")
	callCallbackFn = mustAttr("call_callback_add")
	returnsAnErrFn = mustAttr("returns_an_error")

	moduleLoadNs = time.Since(start).Nanoseconds()
	pythonVersionStr = PyVersion()

	// Release the GIL so subtest goroutines (on different OS threads)
	// can acquire it. Each subtest calls ensureThread(t).
	PySaveThread()

	// --- Run tests ---
	code := m.Run()

	// --- Cleanup ---
	// Reacquire GIL for finalization
	PyEnsureGIL()
	PyFinalize()
	os.Exit(code)
}

// mustAttr loads an attribute from pyMod; aborts on failure (fail-fast).
func mustAttr(name string) pyObj {
	obj, err := PyGetAttr(pyMod, name)
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: module.%s: %v\n", name, err)
		os.Exit(1)
	}
	return obj
}

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
// Statistics helpers (same schema as MetaFFI benchmark)
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
	OS            string `json:"os"`
	Arch          string `json:"arch"`
	GoVersion     string `json:"go_version"`
	PythonVersion string `json:"python_version"`
}

type Config struct {
	WarmupIterations   int   `json:"warmup_iterations"`
	MeasuredIterations int   `json:"measured_iterations"`
	BatchMinElapsedNs  int64 `json:"batch_min_elapsed_ns"`
	BatchMaxCalls      int   `json:"batch_max_calls"`
	TimerOverheadNs    int64 `json:"timer_overhead_ns"`
}

type InitTiming struct {
	PythonInitNs int64 `json:"python_init_ns"`
	ModuleLoadNs int64 `json:"module_load_ns"`
}

// computeStats computes summary statistics from a sorted slice of nanosecond timings.
func computeStats(sorted []int64) PhaseStats {
	n := len(sorted)
	if n == 0 {
		return PhaseStats{}
	}

	// Mean
	var sum float64
	for _, v := range sorted {
		sum += float64(v)
	}
	mean := sum / float64(n)

	// Median
	var median float64
	if n%2 == 0 {
		median = float64(sorted[n/2-1]+sorted[n/2]) / 2.0
	} else {
		median = float64(sorted[n/2])
	}

	// Percentiles
	p95 := float64(sorted[int(float64(n)*0.95)])
	p99 := float64(sorted[int(math.Min(float64(n)*0.99, float64(n-1)))])

	// Stddev
	var sqDiffSum float64
	for _, v := range sorted {
		diff := float64(v) - mean
		sqDiffSum += diff * diff
	}
	stddev := math.Sqrt(sqDiffSum / float64(n))

	// 95% confidence interval
	se := stddev / math.Sqrt(float64(n))
	ci95Low := mean - 1.96*se
	ci95High := mean + 1.96*se

	return PhaseStats{
		MeanNs:   mean,
		MedianNs: median,
		P95Ns:    p95,
		P99Ns:    p99,
		StddevNs: stddev,
		CI95Ns:   [2]float64{ci95Low, ci95High},
	}
}

// removeOutliersIQR removes IQR-based outliers from a sorted slice.
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

// measureTimerOverhead estimates the overhead of time.Now()/time.Since().
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
// Benchmark runner (fail-fast: any incorrect result aborts immediately)
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

	// Sort for statistics
	sortedNs := make([]int64, len(rawNs))
	copy(sortedNs, rawNs)
	sort.Slice(sortedNs, func(i, j int) bool { return sortedNs[i] < sortedNs[j] })

	// Remove outliers
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

// ensureThread locks the goroutine to the current OS thread and acquires
// the Python GIL. The GIL is released automatically when the subtest ends.
// Must be called at the start of each subtest since t.Run() creates new
// goroutines on potentially different OS threads.
func ensureThread(t *testing.T) {
	t.Helper()
	runtime.LockOSThread()
	state := PyEnsureGIL()
	t.Cleanup(func() {
		PyReleaseGIL(state)
	})
}

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
		ensureThread(t)
		result := runBenchmark(t, "void_call", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
			return BenchVoidCall(waitABitFunc)
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 2: Primitive echo ---
	t.Run("primitive_echo", func(t *testing.T) {
		ensureThread(t)
		result := runBenchmark(t, "primitive_echo", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
			return BenchPrimitiveEcho(divIntegersFunc)
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 3: String echo ---
	t.Run("string_echo", func(t *testing.T) {
		ensureThread(t)
		result := runBenchmark(t, "string_echo", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
			return BenchStringEcho(joinStringsFunc)
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 4: Array sum (varying sizes) ---
	for _, size := range []int{10, 100, 1000, 10000} {
		size := size
		t.Run(fmt.Sprintf("array_sum_%d", size), func(t *testing.T) {
			ensureThread(t)
			var expectedSum int64
			for i := 1; i <= size; i++ {
				expectedSum += int64(i)
			}

			sizePtr := size
			result := runBenchmark(t, "array_sum", &sizePtr, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				return BenchArraySum(acceptsRaggedFn, size, expectedSum)
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 5: Object create + method call ---
	t.Run("object_method", func(t *testing.T) {
		ensureThread(t)
		result := runBenchmark(t, "object_method", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
			return BenchObjectMethod(someClassObj)
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 6: Callback invocation ---
	t.Run("callback", func(t *testing.T) {
		ensureThread(t)
		result := runBenchmark(t, "callback", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
			return BenchCallback(callCallbackFn)
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Scenario 7: Error propagation ---
	t.Run("error_propagation", func(t *testing.T) {
		ensureThread(t)
		result := runBenchmark(t, "error_propagation", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
			return BenchErrorPropagation(returnsAnErrFn)
		})
		benchmarks = append(benchmarks, result)
	})

	// --- Write results to JSON ---
	writeResults(t, benchmarks, timerOverhead, warmup, iterations, batchMinElapsedNs, batchMaxCalls)
}

// ---------------------------------------------------------------------------
// JSON output
// ---------------------------------------------------------------------------

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
		resultPath = filepath.Join("..", "..", "..", "results", "go_to_python3_cpython.json")
	}

	result := ResultFile{
		Metadata: Metadata{
			Host:      "go",
			Guest:     "python3",
			Mechanism: "cpython",
			Timestamp: time.Now().UTC().Format(time.RFC3339),
			Environment: Environment{
				OS:            runtime.GOOS,
				Arch:          runtime.GOARCH,
				GoVersion:     runtime.Version(),
				PythonVersion: pythonVersionStr,
			},
			Config: Config{
				WarmupIterations:   warmup,
				MeasuredIterations: iterations,
				BatchMinElapsedNs:  batchMinElapsedNs,
				BatchMaxCalls:      batchMaxCalls,
				TimerOverheadNs:    timerOverhead,
			},
		},
		Init: InitTiming{
			PythonInitNs: pyInitNs,
			ModuleLoadNs: moduleLoadNs,
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
