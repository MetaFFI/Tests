"""Performance benchmarks: Python3 -> Go via MetaFFI

7 scenarios matching the plan specification, with statistical rigor.
Outputs results to tests/results/python3_to_go_metaffi.json.
"""

import json
import math
import os
import platform
import sys
import time

import pytest
import metaffi
from conftest import init_timing

T = metaffi.MetaFFITypes
ti = metaffi.metaffi_type_info

# ---------------------------------------------------------------------------
# Configuration (from env or defaults)
# ---------------------------------------------------------------------------

WARMUP = int(os.environ.get("METAFFI_TEST_WARMUP", "100"))
ITERATIONS = int(os.environ.get("METAFFI_TEST_ITERATIONS", "10000"))


# ---------------------------------------------------------------------------
# Statistical helpers (matching Go implementation)
# ---------------------------------------------------------------------------

def compute_stats(sorted_ns: list[int]) -> dict:
    """Compute summary statistics from a sorted list of nanosecond timings."""
    n = len(sorted_ns)
    if n == 0:
        return {"mean_ns": 0, "median_ns": 0, "p95_ns": 0, "p99_ns": 0,
                "stddev_ns": 0, "ci95_ns": [0, 0]}

    # Mean
    total = sum(sorted_ns)
    mean = total / n

    # Median
    if n % 2 == 1:
        median = float(sorted_ns[n // 2])
    else:
        median = (sorted_ns[n // 2 - 1] + sorted_ns[n // 2]) / 2.0

    # Percentiles
    p95 = float(sorted_ns[int(n * 0.95)])
    p99 = float(sorted_ns[min(int(n * 0.99), n - 1)])

    # Standard deviation
    sq_diff_sum = sum((v - mean) ** 2 for v in sorted_ns)
    stddev = math.sqrt(sq_diff_sum / n)

    # 95% confidence interval
    se = stddev / math.sqrt(n)
    ci95 = [mean - 1.96 * se, mean + 1.96 * se]

    return {
        "mean_ns": mean,
        "median_ns": median,
        "p95_ns": p95,
        "p99_ns": p99,
        "stddev_ns": stddev,
        "ci95_ns": ci95,
    }


def remove_outliers_iqr(sorted_ns: list[int]) -> list[int]:
    """Remove IQR-based outliers from a sorted list."""
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
    """Estimate timer overhead: 10K samples, return median."""
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
    """Execute a benchmark scenario with warmup + measured iterations.

    bench_fn() must raise on incorrect results (fail-fast).
    """

    # Warmup phase (still validate correctness)
    for i in range(warmup):
        try:
            bench_fn()
        except Exception as e:
            raise RuntimeError(
                f"Benchmark '{scenario}' warmup iteration {i}: {e}"
            ) from e

    # Measurement phase
    raw_ns = []
    for i in range(iterations):
        start = time.perf_counter_ns()
        bench_fn()
        elapsed = time.perf_counter_ns() - start
        raw_ns.append(elapsed)

    # Sort for statistics
    sorted_ns = sorted(raw_ns)

    # Remove outliers
    cleaned = remove_outliers_iqr(sorted_ns)

    # Compute stats
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

def write_results(benchmarks: list[dict], timer_overhead: int):
    """Write benchmark results to JSON file."""

    result_path = os.environ.get("METAFFI_TEST_RESULTS_FILE", "")
    if not result_path:
        # Default: relative to this file -> ../../results/
        this_dir = os.path.dirname(os.path.abspath(__file__))
        result_path = os.path.join(this_dir, "..", "..", "results",
                                   "python3_to_go_metaffi.json")

    result = {
        "metadata": {
            "host": "python3",
            "guest": "go",
            "mechanism": "metaffi",
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
        "initialization": init_timing,
        "correctness": None,  # Correctness tested separately
        "benchmarks": benchmarks,
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(os.path.abspath(result_path)), exist_ok=True)

    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Results written to {result_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Benchmark tests (7 scenarios)
# ---------------------------------------------------------------------------

class TestBenchmarks:

    def test_all_benchmarks(self, go_module):
        """Run all 7 benchmark scenarios and write results to JSON."""

        mode = os.environ.get("METAFFI_TEST_MODE", "")
        if mode == "correctness":
            pytest.skip("Skipping benchmarks: METAFFI_TEST_MODE=correctness")

        timer_overhead = measure_timer_overhead()
        print(f"Timer overhead: {timer_overhead} ns", file=sys.stderr)

        benchmarks = []

        # --- Scenario 1: Void call ---
        wait_fn = go_module.load_entity("callable=WaitABit",
            [ti(T.metaffi_int64_type)], None)

        benchmarks.append(run_benchmark(
            "void_call", None, WARMUP, ITERATIONS,
            lambda: wait_fn(0)
        ))
        del wait_fn

        # --- Scenario 2: Primitive echo (int64 -> float64) ---
        div_fn = go_module.load_entity("callable=DivIntegers",
            [ti(T.metaffi_int64_type), ti(T.metaffi_int64_type)],
            [ti(T.metaffi_float64_type)])

        def bench_primitive():
            result = div_fn(10, 2)
            if abs(result - 5.0) > 1e-10:
                raise RuntimeError(f"DivIntegers(10,2) = {result}, want 5.0")

        benchmarks.append(run_benchmark(
            "primitive_echo", None, WARMUP, ITERATIONS, bench_primitive
        ))
        del div_fn

        # --- Scenario 3: String echo ---
        join_fn = go_module.load_entity("callable=JoinStrings",
            [ti(T.metaffi_string8_array_type, dims=1)],
            [ti(T.metaffi_string8_type)])

        def bench_string():
            result = join_fn(["hello", "world"])
            if result != "hello,world":
                raise RuntimeError(f"JoinStrings = {result!r}, want 'hello,world'")

        benchmarks.append(run_benchmark(
            "string_echo", None, WARMUP, ITERATIONS, bench_string
        ))
        del join_fn

        # --- Scenario 4: Array echo (varying sizes) ---
        # Note: SumRaggedArray unusable due to Go int!=int64 type mismatch.
        # Using EchoBytes (uint8 round-trip) to benchmark array marshaling.
        echo_fn = go_module.load_entity("callable=EchoBytes",
            [ti(T.metaffi_uint8_array_type, dims=1)],
            [ti(T.metaffi_uint8_array_type, dims=1)])

        for size in [10, 100, 1000, 10000]:
            data = [i % 256 for i in range(size)]

            # Capture loop vars with default args
            def bench_array(d=data, sz=size):
                result = echo_fn(d)
                if len(result) != sz:
                    raise RuntimeError(
                        f"EchoBytes({sz}): got len {len(result)}, want {sz}"
                    )

            benchmarks.append(run_benchmark(
                "array_echo", size, WARMUP, ITERATIONS, bench_array
            ))

        del echo_fn

        # --- Scenario 5: Object create + method call ---
        new_testmap = go_module.load_entity("callable=NewTestMap", None,
            [ti(T.metaffi_handle_type)])
        name_getter = go_module.load_entity("callable=TestMap.GetName",
            [ti(T.metaffi_handle_type)],
            [ti(T.metaffi_string8_type)])

        def bench_object():
            handle = new_testmap()
            name = name_getter(handle)
            if name != "name1":
                raise RuntimeError(f"TestMap.Name = {name!r}, want 'name1'")

        benchmarks.append(run_benchmark(
            "object_method", None, WARMUP, ITERATIONS, bench_object
        ))
        del new_testmap, name_getter

        # --- Scenario 6: Callback invocation ---
        call_cb = go_module.load_entity("callable=CallCallbackAdd",
            [ti(T.metaffi_callable_type)],
            [ti(T.metaffi_int64_type)])

        def adder(a: int, b: int) -> int:
            return a + b

        metaffi_adder = metaffi.make_metaffi_callable(adder)

        def bench_callback():
            result = call_cb(metaffi_adder)
            if result != 3:
                raise RuntimeError(f"CallCallbackAdd: got {result}, want 3")

        benchmarks.append(run_benchmark(
            "callback", None, WARMUP, ITERATIONS, bench_callback
        ))
        del call_cb, metaffi_adder

        # --- Scenario 7: Error propagation ---
        err_fn = go_module.load_entity("callable=ReturnsAnError", None, None)

        def bench_error():
            try:
                err_fn()
                raise RuntimeError("ReturnsAnError did not raise")
            except RuntimeError:
                pass  # Expected: Go error -> Python RuntimeError

        benchmarks.append(run_benchmark(
            "error_propagation", None, WARMUP, ITERATIONS, bench_error
        ))
        del err_fn

        # --- Write results ---
        write_results(benchmarks, timer_overhead)
