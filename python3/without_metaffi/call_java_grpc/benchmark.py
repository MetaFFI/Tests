"""Performance benchmarks: Python3 -> Java via gRPC (baseline)

7 scenarios matching the MetaFFI benchmark.
Starts a Java gRPC server as a subprocess, benchmarks from Python client.
Outputs results to tests/results/python3_to_java_grpc.json.
"""

import json
import math
import os
import platform
import subprocess
import sys
import time
import threading
import queue

import grpc
from google.protobuf import struct_pb2

# Add this directory to sys.path so generated stubs are importable
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

import benchmark_pb2
import benchmark_pb2_grpc

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WARMUP = int(os.environ.get("METAFFI_TEST_WARMUP", "100"))
ITERATIONS = int(os.environ.get("METAFFI_TEST_ITERATIONS", "10000"))


def _parse_scenario_filter() -> set[str] | None:
    raw = os.environ.get("METAFFI_TEST_SCENARIOS", "").strip()
    if not raw:
        return None
    items = {part.strip() for part in raw.split(",") if part.strip()}
    return items or None


def _scenario_key(name: str, data_size: int | None) -> str:
    return f"{name}_{data_size}" if data_size is not None else name


def _should_run(filter_set: set[str] | None, name: str, data_size: int | None) -> bool:
    if not filter_set:
        return True
    return _scenario_key(name, data_size) in filter_set

METAFFI_SOURCE_ROOT = os.environ.get("METAFFI_SOURCE_ROOT")
if not METAFFI_SOURCE_ROOT:
    raise RuntimeError("METAFFI_SOURCE_ROOT environment variable not set.")

# Java gRPC server JAR (built by Go->Java gRPC tests via Maven)
SERVER_DIR = os.path.join(
    METAFFI_SOURCE_ROOT, "tests", "go", "without_metaffi",
    "call_java_grpc", "server"
)
FAT_JAR = os.path.join(SERVER_DIR, "target", "benchmark-server-1.0-SNAPSHOT.jar")
GUEST_JAR = os.path.join(
    METAFFI_SOURCE_ROOT, "sdk", "test_modules", "guest_modules", "java",
    "test_bin", "guest_java.jar"
)


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

class JavaGrpcServer:
    """Manages the Java gRPC server subprocess."""

    def __init__(self):
        self.process = None
        self.port = None

    def start(self):
        """Start the Java gRPC server and wait for READY:<port>."""
        if not os.path.isfile(FAT_JAR):
            raise RuntimeError(
                f"Java gRPC server JAR not found: {FAT_JAR}\n"
                "Build it first: cd tests/go/without_metaffi/call_java_grpc/server "
                "&& mvn package -q"
            )

        if not os.path.isfile(GUEST_JAR):
            raise RuntimeError(f"Guest JAR not found: {GUEST_JAR}")

        # Build classpath: fat JAR + guest JAR
        classpath = FAT_JAR + os.pathsep + GUEST_JAR

        java_exe = os.environ.get("JAVA_EXE", "java")
        self.process = subprocess.Popen(
            [java_exe, "-cp", classpath,
             "benchmark.BenchmarkServer", "--port", "0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=SERVER_DIR,
        )

        # Read READY:<port> from stdout
        line = self.process.stdout.readline().decode().strip()
        if not line.startswith("READY:"):
            self.stop()
            raise RuntimeError(
                f"Server did not print READY:<port>, got: {line!r}")

        self.port = int(line.split(":")[1])

        # Drain stdout/stderr in background to prevent blocking
        def drain(stream):
            for _ in stream:
                pass
        threading.Thread(target=drain, args=(self.process.stdout,),
                         daemon=True).start()
        threading.Thread(target=drain, args=(self.process.stderr,),
                         daemon=True).start()

    def stop(self):
        """Kill the server process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def address(self) -> str:
        return f"127.0.0.1:{self.port}"


# ---------------------------------------------------------------------------
# Statistical helpers (matching MetaFFI implementation)
# ---------------------------------------------------------------------------

def compute_stats(sorted_ns: list[int]) -> dict:
    n = len(sorted_ns)
    if n == 0:
        return {"mean_ns": 0, "median_ns": 0, "p95_ns": 0, "p99_ns": 0,
                "stddev_ns": 0, "ci95_ns": [0, 0]}

    total = sum(sorted_ns)
    mean = total / n

    if n % 2 == 1:
        median = float(sorted_ns[n // 2])
    else:
        median = (sorted_ns[n // 2 - 1] + sorted_ns[n // 2]) / 2.0

    p95 = float(sorted_ns[int(n * 0.95)])
    p99 = float(sorted_ns[min(int(n * 0.99), n - 1)])

    sq_diff_sum = sum((v - mean) ** 2 for v in sorted_ns)
    stddev = math.sqrt(sq_diff_sum / n)

    se = stddev / math.sqrt(n)
    ci95 = [mean - 1.96 * se, mean + 1.96 * se]

    return {
        "mean_ns": mean, "median_ns": median,
        "p95_ns": p95, "p99_ns": p99,
        "stddev_ns": stddev, "ci95_ns": ci95,
    }


def remove_outliers_iqr(sorted_ns: list[int]) -> list[int]:
    n = len(sorted_ns)
    if n < 4:
        return sorted_ns

    q1 = float(sorted_ns[n // 4])
    q3 = float(sorted_ns[3 * n // 4])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    return [v for v in sorted_ns if lower <= v <= upper]


def measure_timer_overhead() -> int:
    samples = []
    for _ in range(10000):
        start = time.perf_counter_ns()
        elapsed = time.perf_counter_ns() - start
        samples.append(elapsed)
    samples.sort()
    return samples[5000]


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_benchmark(scenario: str, data_size: int | None,
                  warmup: int, iterations: int,
                  bench_fn: callable) -> dict:

    for i in range(warmup):
        try:
            bench_fn()
        except Exception as e:
            raise RuntimeError(
                f"Benchmark '{scenario}' warmup iteration {i}: {e}"
            ) from e

    raw_ns = []
    for i in range(iterations):
        start = time.perf_counter_ns()
        bench_fn()
        elapsed = time.perf_counter_ns() - start
        raw_ns.append(elapsed)

    sorted_ns = sorted(raw_ns)
    cleaned = remove_outliers_iqr(sorted_ns)
    total_stats = compute_stats(cleaned)

    return {
        "scenario": scenario,
        "data_size": data_size,
        "status": "PASS",
        "raw_iterations_ns": raw_ns,
        "phases": {"total": total_stats},
    }


# ---------------------------------------------------------------------------
# Result writer
# ---------------------------------------------------------------------------

def write_results(benchmarks: list[dict], timer_overhead: int, init_ns: int):
    result_path = os.environ.get("METAFFI_TEST_RESULTS_FILE", "")
    if not result_path:
        result_path = os.path.join(THIS_DIR, "..", "..", "..", "results",
                                   "python3_to_java_grpc.json")

    result = {
        "metadata": {
            "host": "python3",
            "guest": "java",
            "mechanism": "grpc",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "environment": {
                "os": platform.system().lower(),
                "arch": platform.machine(),
                "python_version": platform.python_version(),
            },
            "config": {
                "warmup_iterations": WARMUP,
                "measured_iterations": ITERATIONS,
                "timer_overhead_ns": timer_overhead,
            },
        },
        "initialization": {
            "server_start_ns": init_ns,
        },
        "correctness": None,
        "benchmarks": benchmarks,
    }

    os.makedirs(os.path.dirname(os.path.abspath(result_path)), exist_ok=True)
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Results written to {result_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------

def main():
    mode = os.environ.get("METAFFI_TEST_MODE", "")
    if mode == "correctness":
        print("Skipping benchmarks: METAFFI_TEST_MODE=correctness",
              file=sys.stderr)
        return

    # Start Java gRPC server
    server = JavaGrpcServer()
    init_start = time.perf_counter_ns()
    server.start()
    init_ns = time.perf_counter_ns() - init_start
    print(f"Server started on {server.address()} in {init_ns / 1e6:.1f} ms",
          file=sys.stderr)

    try:
        # Connect to server
        channel = grpc.insecure_channel(server.address())
        stub = benchmark_pb2_grpc.BenchmarkServiceStub(channel)

        timer_overhead = measure_timer_overhead()
        print(f"Timer overhead: {timer_overhead} ns", file=sys.stderr)

        benchmarks = []
        scenario_filter = _parse_scenario_filter()
        selected_count = 0
        if scenario_filter:
            print(
                "Scenario filter enabled: " + os.environ.get("METAFFI_TEST_SCENARIOS", ""),
                file=sys.stderr,
            )

        # --- Scenario 1: Void call ---
        void_req = benchmark_pb2.VoidCallRequest()

        def bench_void():
            stub.VoidCall(void_req)

        if _should_run(scenario_filter, "void_call", None):
            selected_count += 1
            benchmarks.append(run_benchmark(
                "void_call", None, WARMUP, ITERATIONS, bench_void
            ))

        # --- Scenario 2: Primitive echo ---
        div_req = benchmark_pb2.DivIntegersRequest(x=10, y=2)

        def bench_primitive():
            resp = stub.DivIntegers(div_req)
            if abs(resp.result - 5.0) > 1e-10:
                raise RuntimeError(f"DivIntegers: {resp.result}, want 5.0")

        if _should_run(scenario_filter, "primitive_echo", None):
            selected_count += 1
            benchmarks.append(run_benchmark(
                "primitive_echo", None, WARMUP, ITERATIONS, bench_primitive
            ))

        # --- Scenario 3: String echo ---
        join_req = benchmark_pb2.JoinStringsRequest(values=["hello", "world"])

        def bench_string():
            resp = stub.JoinStrings(join_req)
            if resp.result != "hello,world":
                raise RuntimeError(f"JoinStrings: {resp.result!r}")

        if _should_run(scenario_filter, "string_echo", None):
            selected_count += 1
            benchmarks.append(run_benchmark(
                "string_echo", None, WARMUP, ITERATIONS, bench_string
            ))

        # --- Scenario 4: Array sum (varying sizes) ---
        for size in [10, 100, 1000, 10000]:
            if not _should_run(scenario_filter, "array_sum", size):
                continue
            selected_count += 1
            values = list(range(1, size + 1))
            expected = size * (size + 1) // 2
            req = benchmark_pb2.ArraySumRequest(values=values)

            def bench_array(r=req, e=expected, sz=size):
                resp = stub.ArraySum(r)
                if resp.sum != e:
                    raise RuntimeError(
                        f"ArraySum({sz}): got {resp.sum}, want {e}"
                    )

            benchmarks.append(run_benchmark(
                "array_sum", size, WARMUP, ITERATIONS, bench_array
            ))

        # --- Scenario: Dynamic Any echo (mixed array payload) ---
        any_echo_size = 100
        if _should_run(scenario_filter, "any_echo", any_echo_size):
            selected_count += 1
            values = []
            for i in range(any_echo_size):
                mod = i % 3
                if mod == 0:
                    values.append(struct_pb2.Value(number_value=1.0))
                elif mod == 1:
                    values.append(struct_pb2.Value(string_value="two"))
                else:
                    values.append(struct_pb2.Value(number_value=3.0))

            any_req = benchmark_pb2.AnyEchoRequest(
                values=struct_pb2.ListValue(values=values)
            )

            def bench_any_echo(r=any_req, expected_len=any_echo_size):
                resp = stub.AnyEcho(r)
                if len(resp.values.values) != expected_len:
                    raise RuntimeError(
                        f"AnyEcho: got len {len(resp.values.values)}, want {expected_len}"
                    )

            benchmarks.append(run_benchmark(
                "any_echo", any_echo_size, WARMUP, ITERATIONS, bench_any_echo
            ))

        # --- Scenario 5: Object method ---
        obj_req = benchmark_pb2.ObjectMethodRequest(name="bench")

        def bench_object():
            resp = stub.ObjectMethod(obj_req)
            if resp.result != "Hello from SomeClass bench":
                raise RuntimeError(
                    f"ObjectMethod: {resp.result!r}")

        if _should_run(scenario_filter, "object_method", None):
            selected_count += 1
            benchmarks.append(run_benchmark(
                "object_method", None, WARMUP, ITERATIONS, bench_object
            ))

        # --- Scenario 6: Callback via bidirectional streaming ---
        def bench_callback():
            send_q = queue.Queue()
            recv_q = queue.Queue()

            def request_gen():
                while True:
                    msg = send_q.get()
                    if msg is None:
                        return
                    yield msg

            def run_stream():
                try:
                    responses = stub.CallbackAdd(request_gen())
                    for resp in responses:
                        recv_q.put(resp)
                except Exception as e:
                    recv_q.put(e)

            t = threading.Thread(target=run_stream, daemon=True)
            t.start()

            # Step 1: Send invoke
            send_q.put(benchmark_pb2.CallbackClientMsg(invoke=True))

            # Step 2: Receive compute(a, b)
            resp = recv_q.get(timeout=5)
            if isinstance(resp, Exception):
                raise resp
            compute = resp.compute
            result = compute.a + compute.b

            # Step 3: Send result
            send_q.put(
                benchmark_pb2.CallbackClientMsg(add_result=result))

            # Step 4: Receive final result
            resp = recv_q.get(timeout=5)
            if isinstance(resp, Exception):
                raise resp
            final = resp.final_result

            if final != 3:
                raise RuntimeError(f"Callback: got {final}, want 3")

            # Close stream
            send_q.put(None)
            t.join(timeout=5)

        if _should_run(scenario_filter, "callback", None):
            selected_count += 1
            benchmarks.append(run_benchmark(
                "callback", None, WARMUP, ITERATIONS, bench_callback
            ))

        # --- Scenario 7: Error propagation ---
        empty_req = benchmark_pb2.Empty()

        def bench_error():
            try:
                stub.ReturnsAnError(empty_req)
                raise RuntimeError("ReturnsAnError did not raise")
            except grpc.RpcError as e:
                if e.code() != grpc.StatusCode.INTERNAL:
                    raise RuntimeError(
                        f"Expected INTERNAL, got {e.code()}")

        if _should_run(scenario_filter, "error_propagation", None):
            selected_count += 1
            benchmarks.append(run_benchmark(
                "error_propagation", None, WARMUP, ITERATIONS, bench_error
            ))

        if scenario_filter and selected_count == 0:
            raise RuntimeError(
                "METAFFI_TEST_SCENARIOS selected no benchmark scenarios: "
                + os.environ.get("METAFFI_TEST_SCENARIOS", "")
            )

        # --- Write results ---
        write_results(benchmarks, timer_overhead, init_ns)

        # Cleanup
        channel.close()

    finally:
        server.stop()


if __name__ == "__main__":
    main()
