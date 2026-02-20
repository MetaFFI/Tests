package call_java_grpc

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
	"testing"
	"time"

	pb "github.com/MetaFFI/tests/go/without_metaffi/call_java_grpc/pb"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/protobuf/types/known/structpb"
)

// ---------------------------------------------------------------------------
// Global state
// ---------------------------------------------------------------------------

var (
	client     pb.BenchmarkServiceClient
	conn       *grpc.ClientConn
	serverCmd  *exec.Cmd
	serverAddr string

	// Init timing
	serverStartNs int64
	connectNs     int64
)

// ---------------------------------------------------------------------------
// TestMain -- build Java gRPC server, start it, connect, run tests, stop
// ---------------------------------------------------------------------------

func TestMain(m *testing.M) {
	srcRoot := os.Getenv("METAFFI_SOURCE_ROOT")
	if srcRoot == "" {
		fmt.Fprintln(os.Stderr, "FATAL: METAFFI_SOURCE_ROOT must be set")
		os.Exit(1)
	}

	guestJarPath := filepath.Join(srcRoot, "sdk", "test_modules", "guest_modules", "java", "test_bin", "guest_java.jar")

	// Verify guest JAR exists
	if _, err := os.Stat(guestJarPath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "FATAL: guest_java.jar not found at %s\n", guestJarPath)
		os.Exit(1)
	}

	// Resolve server directory
	serverDir := filepath.Join(getTestDir(), "server")

	// --- Build Java gRPC server (Maven shade) ---
	fatJar := filepath.Join(serverDir, "target", "benchmark-server-1.0-SNAPSHOT.jar")

	// Build only if JAR doesn't already exist
	if _, err := os.Stat(fatJar); os.IsNotExist(err) {
		fmt.Fprintln(os.Stderr, "Building Java gRPC server...")
		buildStart := time.Now()

		mvnExe := os.Getenv("MVN_EXE")
		if mvnExe == "" {
			mvnExe = "mvn"
		}

		buildCmd := exec.Command(mvnExe, "package", "-q")
		buildCmd.Dir = serverDir
		buildCmd.Stdout = os.Stderr
		buildCmd.Stderr = os.Stderr
		buildCmd.Env = append(os.Environ(), "METAFFI_SOURCE_ROOT="+srcRoot)
		if err := buildCmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "FATAL: failed to build Java gRPC server: %v\n", err)
			os.Exit(1)
		}
		fmt.Fprintf(os.Stderr, "Java gRPC server built in %d ms\n", time.Since(buildStart).Milliseconds())
	} else {
		fmt.Fprintln(os.Stderr, "Java gRPC server JAR already exists, skipping build")
	}

	// Verify fat JAR exists
	if _, err := os.Stat(fatJar); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "FATAL: fat JAR not found at %s\n", fatJar)
		os.Exit(1)
	}

	// --- Start Java gRPC server ---
	startTime := time.Now()

	// Build classpath: fat JAR + guest JAR
	cpSep := string(os.PathListSeparator)
	classpath := fatJar + cpSep + guestJarPath

	javaExe := os.Getenv("JAVA_EXE")
	if javaExe == "" {
		javaExe = "java"
	}

	serverCmd = exec.Command(javaExe, "-cp", classpath, "benchmark.BenchmarkServer", "--port", "0")
	serverCmd.Dir = serverDir
	serverCmd.Stderr = os.Stderr

	stdout, err := serverCmd.StdoutPipe()
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: failed to get stdout pipe: %v\n", err)
		os.Exit(1)
	}

	if err := serverCmd.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: failed to start Java gRPC server: %v\n", err)
		os.Exit(1)
	}

	// Read "READY:<port>" from stdout
	scanner := bufio.NewScanner(stdout)
	if !scanner.Scan() {
		serverCmd.Process.Kill()
		fmt.Fprintln(os.Stderr, "FATAL: Java gRPC server did not print READY line")
		os.Exit(1)
	}

	line := scanner.Text()
	if !strings.HasPrefix(line, "READY:") {
		serverCmd.Process.Kill()
		fmt.Fprintf(os.Stderr, "FATAL: unexpected server output: %q\n", line)
		os.Exit(1)
	}
	port := strings.TrimPrefix(line, "READY:")
	serverAddr = "localhost:" + port
	serverStartNs = time.Since(startTime).Nanoseconds()

	// Drain remaining stdout in background
	go func() { io.Copy(io.Discard, stdout) }()

	// --- Connect to server ---
	connectStart := time.Now()
	conn, err = grpc.NewClient(
		serverAddr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		serverCmd.Process.Kill()
		fmt.Fprintf(os.Stderr, "FATAL: failed to connect to gRPC server at %s: %v\n", serverAddr, err)
		os.Exit(1)
	}
	client = pb.NewBenchmarkServiceClient(conn)

	// Verify connectivity with a ping
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	_, pingErr := client.VoidCall(ctx, &pb.VoidCallRequest{Secs: 0})
	cancel()
	if pingErr != nil {
		conn.Close()
		serverCmd.Process.Kill()
		fmt.Fprintf(os.Stderr, "FATAL: Java gRPC server not responding: %v\n", pingErr)
		os.Exit(1)
	}
	connectNs = time.Since(connectStart).Nanoseconds()

	fmt.Fprintf(os.Stderr, "Server start: %d ms, connect: %d ms\n",
		serverStartNs/1e6, connectNs/1e6)

	// --- Run tests ---
	code := m.Run()

	// --- Cleanup ---
	conn.Close()
	serverCmd.Process.Kill()
	serverCmd.Wait()
	os.Exit(code)
}

func getTestDir() string {
	dir, err := os.Getwd()
	if err != nil {
		return "."
	}
	return dir
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
	BatchMinElapsedNs  int64 `json:"batch_min_elapsed_ns"`
	BatchMaxCalls      int   `json:"batch_max_calls"`
	TimerOverheadNs    int64 `json:"timer_overhead_ns"`
}

type InitTiming struct {
	ServerStartNs int64 `json:"server_start_ns"`
	ConnectNs     int64 `json:"connect_ns"`
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

	for i := 0; i < warmup; i++ {
		if err := benchFn(); err != nil {
			t.Fatalf("benchmark %q warmup iteration %d: %v", scenario, i, err)
			return BenchmarkResult{Scenario: scenario, DataSize: dataSize, Status: "FAIL"}
		}
	}

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
	scenarioFilter := parseScenarioFilter()
	selectedCount := 0
	if len(scenarioFilter) > 0 {
		t.Logf("Scenario filter enabled: %s", os.Getenv("METAFFI_TEST_SCENARIOS"))
	}

	// --- Scenario 1: Void call ---
	if shouldRunScenario(scenarioFilter, "void_call", nil) {
		selectedCount++
		t.Run("void_call", func(t *testing.T) {
			result := runBenchmark(t, "void_call", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				_, err := client.VoidCall(context.Background(), &pb.VoidCallRequest{})
				return err
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 2: Primitive echo ---
	if shouldRunScenario(scenarioFilter, "primitive_echo", nil) {
		selectedCount++
		t.Run("primitive_echo", func(t *testing.T) {
			result := runBenchmark(t, "primitive_echo", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				resp, err := client.DivIntegers(context.Background(), &pb.DivIntegersRequest{X: 10, Y: 2})
				if err != nil {
					return err
				}
				if math.Abs(resp.Result-5.0) > 1e-10 {
					return fmt.Errorf("divIntegers: got %v, want 5.0", resp.Result)
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 3: String echo ---
	if shouldRunScenario(scenarioFilter, "string_echo", nil) {
		selectedCount++
		t.Run("string_echo", func(t *testing.T) {
			result := runBenchmark(t, "string_echo", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				resp, err := client.JoinStrings(context.Background(), &pb.JoinStringsRequest{
					Values: []string{"hello", "world"},
				})
				if err != nil {
					return err
				}
				if resp.Result != "hello,world" {
					return fmt.Errorf("joinStrings: got %q, want \"hello,world\"", resp.Result)
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 4: Array sum (varying sizes) ---
	for _, size := range []int{10, 100, 1000, 10000} {
		size := size
		sizePtr := size
		if !shouldRunScenario(scenarioFilter, "array_sum", &sizePtr) {
			continue
		}
		selectedCount++
		t.Run(fmt.Sprintf("array_sum_%d", size), func(t *testing.T) {
			// Pre-build the values slice
			values := make([]int64, size)
			var expectedSum int64
			for i := 0; i < size; i++ {
				values[i] = int64(i + 1)
				expectedSum += int64(i + 1)
			}

			result := runBenchmark(t, "array_sum", &sizePtr, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				resp, err := client.ArraySum(context.Background(), &pb.ArraySumRequest{
					Values: values,
				})
				if err != nil {
					return err
				}
				if resp.Sum != expectedSum {
					return fmt.Errorf("array_sum: got %d, want %d", resp.Sum, expectedSum)
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario: Dynamic any echo (mixed array payload) ---
	{
		anyEchoSize := 100
		if shouldRunScenario(scenarioFilter, "any_echo", &anyEchoSize) {
			selectedCount++
			t.Run("any_echo_100", func(t *testing.T) {
				values := &structpb.ListValue{Values: make([]*structpb.Value, 0, anyEchoSize)}
				for i := 0; i < anyEchoSize; i++ {
					switch i % 3 {
					case 0:
						values.Values = append(values.Values, structpb.NewNumberValue(1))
					case 1:
						values.Values = append(values.Values, structpb.NewStringValue("two"))
					default:
						values.Values = append(values.Values, structpb.NewNumberValue(3.0))
					}
				}
				req := &pb.AnyEchoRequest{Values: values}
				sizePtr := anyEchoSize
				result := runBenchmark(t, "any_echo", &sizePtr, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
					resp, err := client.AnyEcho(context.Background(), req)
					if err != nil {
						return err
					}
					if resp.GetValues() == nil || len(resp.GetValues().GetValues()) != anyEchoSize {
						return fmt.Errorf("AnyEcho: got len %d, want %d", len(resp.GetValues().GetValues()), anyEchoSize)
					}
					return nil
				})
				benchmarks = append(benchmarks, result)
			})
		}
	}

	// --- Scenario 5: Object create + method call ---
	if shouldRunScenario(scenarioFilter, "object_method", nil) {
		selectedCount++
		t.Run("object_method", func(t *testing.T) {
			result := runBenchmark(t, "object_method", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				resp, err := client.ObjectMethod(context.Background(), &pb.ObjectMethodRequest{
					Name: "bench",
				})
				if err != nil {
					return err
				}
				if resp.Result != "Hello from SomeClass bench" {
					return fmt.Errorf("object_method: got %q, want \"Hello from SomeClass bench\"", resp.Result)
				}
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 6: Callback (bidirectional streaming) ---
	if shouldRunScenario(scenarioFilter, "callback", nil) {
		selectedCount++
		t.Run("callback", func(t *testing.T) {
			result := runBenchmark(t, "callback", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				stream, err := client.CallbackAdd(context.Background())
				if err != nil {
					return fmt.Errorf("open stream: %w", err)
				}

				// Send invoke
				if err := stream.Send(&pb.CallbackClientMsg{
					Msg: &pb.CallbackClientMsg_Invoke{Invoke: true},
				}); err != nil {
					return fmt.Errorf("send invoke: %w", err)
				}

				// Receive compute request
				resp, err := stream.Recv()
				if err != nil {
					return fmt.Errorf("recv compute: %w", err)
				}
				compute := resp.GetCompute()
				if compute == nil {
					return fmt.Errorf("expected compute message, got %v", resp)
				}

				// Compute and send result
				sum := compute.A + compute.B
				if err := stream.Send(&pb.CallbackClientMsg{
					Msg: &pb.CallbackClientMsg_AddResult{AddResult: sum},
				}); err != nil {
					return fmt.Errorf("send result: %w", err)
				}

				// Receive final result
				resp, err = stream.Recv()
				if err != nil {
					return fmt.Errorf("recv final: %w", err)
				}
				if resp.GetFinalResult() != 3 {
					return fmt.Errorf("callback: got %d, want 3", resp.GetFinalResult())
				}

				stream.CloseSend()
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	// --- Scenario 7: Error propagation ---
	if shouldRunScenario(scenarioFilter, "error_propagation", nil) {
		selectedCount++
		t.Run("error_propagation", func(t *testing.T) {
			result := runBenchmark(t, "error_propagation", nil, warmup, iterations, batchMinElapsedNs, batchMaxCalls, func() error {
				_, err := client.ReturnsAnError(context.Background(), &pb.Empty{})
				if err == nil {
					return fmt.Errorf("expected gRPC error but got nil")
				}
				// Error IS expected -- this is the successful path
				return nil
			})
			benchmarks = append(benchmarks, result)
		})
	}

	if len(scenarioFilter) > 0 && selectedCount == 0 {
		t.Fatalf("METAFFI_TEST_SCENARIOS selected no benchmark scenarios: %q", os.Getenv("METAFFI_TEST_SCENARIOS"))
	}

	// --- Write results ---
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
		resultPath = filepath.Join("..", "..", "..", "results", "go_to_java_grpc.json")
	}

	result := ResultFile{
		Metadata: Metadata{
			Host:      "go",
			Guest:     "java",
			Mechanism: "grpc",
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
		Init: InitTiming{
			ServerStartNs: serverStartNs,
			ConnectNs:     connectNs,
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
