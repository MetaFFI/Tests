"""Performance benchmarks: Python3 -> Java via JPype (native baseline)

7 scenarios matching the MetaFFI benchmark, using JPype to call
Java guest module methods directly from Python.
Outputs results to tests/results/python3_to_java_jpype.json.
"""

import json
import math
import os
import platform
import sys
import time

import jpype
import jpype.imports

# ---------------------------------------------------------------------------
# Configuration (from env or defaults)
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

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

METAFFI_SOURCE_ROOT = os.environ.get("METAFFI_SOURCE_ROOT")
if not METAFFI_SOURCE_ROOT:
    raise RuntimeError("METAFFI_SOURCE_ROOT environment variable not set.")

JAVA_GUEST_JAR = os.path.join(
    METAFFI_SOURCE_ROOT, "sdk", "test_modules", "guest_modules", "java",
    "test_bin", "guest_java.jar"
)

if not os.path.isfile(JAVA_GUEST_JAR):
    raise RuntimeError(f"Java guest JAR not found: {JAVA_GUEST_JAR}")


# ---------------------------------------------------------------------------
# JVM lifecycle
# ---------------------------------------------------------------------------

def start_jvm() -> int:
    """Start JPype JVM with guest JAR on classpath. Returns startup time in ns."""
    if jpype.isJVMStarted():
        return 0

    start = time.perf_counter_ns()
    jpype.startJVM(classpath=[JAVA_GUEST_JAR])
    elapsed = time.perf_counter_ns() - start
    return elapsed


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
                                   "python3_to_java_jpype.json")

    result = {
        "metadata": {
            "host": "python3",
            "guest": "java",
            "mechanism": "jpype",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "environment": {
                "os": platform.system().lower(),
                "arch": platform.machine(),
                "python_version": platform.python_version(),
                "jpype_version": jpype.__version__,
            },
            "config": {
                "warmup_iterations": WARMUP,
                "measured_iterations": ITERATIONS,
                "timer_overhead_ns": timer_overhead,
            },
        },
        "initialization": {
            "jvm_start_ns": init_ns,
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

    # Start JVM and measure init time
    init_ns = start_jvm()
    print(f"JVM started in {init_ns / 1e6:.1f} ms", file=sys.stderr)

    # Import Java classes
    from guest import CoreFunctions, ArrayFunctions, SomeClass
    from java.util.function import IntBinaryOperator
    from java.lang import Object as JObject
    from java.lang import Integer as JInteger
    from java.lang import Double as JDouble
    from java.lang import String as JString

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
    def bench_void():
        CoreFunctions.noOp()

    if _should_run(scenario_filter, "void_call", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "void_call", None, WARMUP, ITERATIONS, bench_void
        ))

    # --- Scenario 2: Primitive echo (long, long -> double) ---
    def bench_primitive():
        result = CoreFunctions.divIntegers(10, 2)
        if abs(float(result) - 5.0) > 1e-10:
            raise RuntimeError(f"divIntegers(10,2) = {result}, want 5.0")

    if _should_run(scenario_filter, "primitive_echo", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "primitive_echo", None, WARMUP, ITERATIONS, bench_primitive
        ))

    # --- Scenario 3: String echo ---
    def bench_string():
        result = CoreFunctions.joinStrings(["hello", "world"])
        if str(result) != "hello,world":
            raise RuntimeError(f"joinStrings = {result!r}")

    if _should_run(scenario_filter, "string_echo", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "string_echo", None, WARMUP, ITERATIONS, bench_string
        ))

    # --- Scenario 4: Array sum (varying sizes) ---
    JInt = jpype.JInt
    for size in [10, 100, 1000, 10000]:
        if not _should_run(scenario_filter, "array_sum", size):
            continue
        selected_count += 1
        # Build a Java int[][] with a single row [1..size]
        row = jpype.JArray(JInt)(list(range(1, size + 1)))
        arr = jpype.JArray(jpype.JArray(JInt))([row])
        expected = size * (size + 1) // 2

        def bench_array(a=arr, e=expected):
            result = int(ArrayFunctions.sumRaggedArray(a))
            if result != e:
                raise RuntimeError(
                    f"sumRaggedArray: got {result}, want {e}"
                )

        benchmarks.append(run_benchmark(
            "array_sum", size, WARMUP, ITERATIONS, bench_array
        ))

    # --- Scenario: dynamic any echo (mixed array payload) ---
    any_echo_size = 100
    if _should_run(scenario_filter, "any_echo", any_echo_size):
        selected_count += 1
        payload = jpype.JArray(JObject)(any_echo_size)
        pattern = [JInteger(1), JString("two"), JDouble(3.0)]
        for i in range(any_echo_size):
            payload[i] = pattern[i % len(pattern)]

        def bench_any_echo(data=payload, expected_len=any_echo_size):
            result = CoreFunctions.echoAny(data)
            if result is None:
                raise RuntimeError("echoAny: got null return")
            if len(result) != expected_len:
                raise RuntimeError(f"echoAny: got len {len(result)}, want {expected_len}")

        benchmarks.append(run_benchmark(
            "any_echo", any_echo_size, WARMUP, ITERATIONS, bench_any_echo
        ))

    # --- Scenario 5: Object create + method call ---
    def bench_object():
        obj = SomeClass("bench")
        result = str(obj.print_())
        if result != "Hello from SomeClass bench":
            raise RuntimeError(f"print() = {result!r}")

    if _should_run(scenario_filter, "object_method", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "object_method", None, WARMUP, ITERATIONS, bench_object
        ))

    # --- Scenario 6: Callback invocation ---
    # Create a JPype proxy for IntBinaryOperator
    @jpype.JImplements(IntBinaryOperator)
    class Adder:
        @jpype.JOverride
        def applyAsInt(self, a, b):
            return int(a) + int(b)

    adder = Adder()

    def bench_callback():
        result = int(CoreFunctions.callCallbackAdd(adder))
        if result != 3:
            raise RuntimeError(f"callCallbackAdd: got {result}, want 3")

    if _should_run(scenario_filter, "callback", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "callback", None, WARMUP, ITERATIONS, bench_callback
        ))

    # --- Scenario 7: Error propagation ---
    def bench_error():
        try:
            CoreFunctions.returnsAnError()
            raise RuntimeError("returnsAnError did not raise")
        except jpype.JException:
            pass

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


if __name__ == "__main__":
    main()
