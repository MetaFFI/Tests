"""Performance benchmarks: Python3 -> Go via ctypes (native baseline)

7 scenarios matching the MetaFFI benchmark, using ctypes to call
a cgo-exported .dll/.so directly.
Outputs results to tests/results/python3_to_go_ctypes.json.
"""

import ctypes
import json
import math
import os
import platform
import subprocess
import sys
import time

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
GO_BRIDGE_DIR = os.path.join(THIS_DIR, "go_bridge")
DLL_PATH = os.path.join(GO_BRIDGE_DIR, "bridge.dll")


# ---------------------------------------------------------------------------
# Build the Go shared library if needed
# ---------------------------------------------------------------------------

def ensure_bridge_dll():
    """Build the Go bridge DLL if missing or stale."""
    must_build = not os.path.isfile(DLL_PATH)
    if not must_build:
        dll_mtime = os.path.getmtime(DLL_PATH)
        for root, _dirs, files in os.walk(GO_BRIDGE_DIR):
            for name in files:
                if not name.endswith((".go", ".c", ".h")):
                    continue
                src_path = os.path.join(root, name)
                if os.path.getmtime(src_path) > dll_mtime:
                    must_build = True
                    break
            if must_build:
                break

    if not must_build:
        return

    print(f"Building Go bridge DLL at {DLL_PATH}...", file=sys.stderr)
    result = subprocess.run(
        ["go", "build", "-buildmode=c-shared", "-o", "bridge.dll", "."],
        cwd=GO_BRIDGE_DIR, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to build Go bridge DLL:\n{result.stderr}"
        )
    print("Go bridge DLL built successfully.", file=sys.stderr)


# ---------------------------------------------------------------------------
# Load the DLL and define function signatures
# ---------------------------------------------------------------------------

def load_bridge():
    """Load the Go bridge DLL and set up function signatures."""
    ensure_bridge_dll()
    lib = ctypes.CDLL(DLL_PATH)

    # Scenario 1: void call
    lib.GoWaitABit.argtypes = [ctypes.c_int64]
    lib.GoWaitABit.restype = ctypes.c_int

    lib.GoNoOp.argtypes = []
    lib.GoNoOp.restype = ctypes.c_int

    # Scenario 2: primitive echo
    lib.GoDivIntegers.argtypes = [
        ctypes.c_int64, ctypes.c_int64,
        ctypes.POINTER(ctypes.c_double),
    ]
    lib.GoDivIntegers.restype = ctypes.c_int

    # Scenario 3: string echo
    lib.GoJoinStrings.argtypes = [
        ctypes.POINTER(ctypes.c_char_p), ctypes.c_int,
        ctypes.POINTER(ctypes.c_char_p),
    ]
    lib.GoJoinStrings.restype = ctypes.c_int

    # Scenario 4: array echo (uint8)
    lib.GoEchoBytes.argtypes = [
        ctypes.c_void_p, ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_int),
    ]
    lib.GoEchoBytes.restype = ctypes.c_int

    # Scenario 5: object create + method call
    lib.GoNewTestMap.argtypes = [ctypes.POINTER(ctypes.c_uint64)]
    lib.GoNewTestMap.restype = ctypes.c_int

    lib.GoTestMapGetName.argtypes = [
        ctypes.c_uint64,
        ctypes.POINTER(ctypes.c_char_p),
    ]
    lib.GoTestMapGetName.restype = ctypes.c_int

    lib.GoFreeHandle.argtypes = [ctypes.c_uint64]
    lib.GoFreeHandle.restype = ctypes.c_int

    # Scenario 6: callback
    AddCallbackType = ctypes.CFUNCTYPE(ctypes.c_int64, ctypes.c_int64, ctypes.c_int64)
    lib.GoCallCallbackAdd.argtypes = [
        AddCallbackType,
        ctypes.POINTER(ctypes.c_int64),
    ]
    lib.GoCallCallbackAdd.restype = ctypes.c_int

    # Scenario 7: error propagation
    lib.GoReturnsAnError.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
    lib.GoReturnsAnError.restype = ctypes.c_int

    # Scenario: dynamic any echo (JSON string payload)
    lib.GoAnyEchoJSON.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p)]
    lib.GoAnyEchoJSON.restype = ctypes.c_int

    # Memory management
    lib.GoFreeString.argtypes = [ctypes.c_char_p]
    lib.GoFreeString.restype = None

    lib.GoFreeBytes.argtypes = [ctypes.c_void_p]
    lib.GoFreeBytes.restype = None

    return lib, AddCallbackType


# ---------------------------------------------------------------------------
# Statistical helpers (matching MetaFFI implementation)
# ---------------------------------------------------------------------------

def compute_stats(sorted_ns: list[int]) -> dict:
    """Compute summary statistics from a sorted list of nanosecond timings."""
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
    """Execute a benchmark scenario with warmup + measured iterations."""

    # Warmup phase
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
    """Write benchmark results to JSON file."""

    result_path = os.environ.get("METAFFI_TEST_RESULTS_FILE", "")
    if not result_path:
        result_path = os.path.join(THIS_DIR, "..", "..", "..", "results",
                                   "python3_to_go_ctypes.json")

    result = {
        "metadata": {
            "host": "python3",
            "guest": "go",
            "mechanism": "ctypes",
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
            "load_dll_ns": init_ns,
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
        print("Skipping benchmarks: METAFFI_TEST_MODE=correctness", file=sys.stderr)
        return

    # Load DLL and measure init time
    init_start = time.perf_counter_ns()
    lib, AddCallbackType = load_bridge()
    init_ns = time.perf_counter_ns() - init_start
    print(f"DLL loaded in {init_ns / 1e6:.1f} ms", file=sys.stderr)

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
        ret = lib.GoNoOp()
        if ret != 0:
            raise RuntimeError("GoNoOp failed")

    if _should_run(scenario_filter, "void_call", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "void_call", None, WARMUP, ITERATIONS, bench_void
        ))

    # --- Scenario 2: Primitive echo (int64 -> float64) ---
    out_double = ctypes.c_double()

    def bench_primitive():
        ret = lib.GoDivIntegers(
            ctypes.c_int64(10), ctypes.c_int64(2),
            ctypes.byref(out_double)
        )
        if ret != 0:
            raise RuntimeError("GoDivIntegers failed")
        if abs(out_double.value - 5.0) > 1e-10:
            raise RuntimeError(f"DivIntegers(10,2) = {out_double.value}, want 5.0")

    if _should_run(scenario_filter, "primitive_echo", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "primitive_echo", None, WARMUP, ITERATIONS, bench_primitive
        ))

    # --- Scenario 3: String echo ---
    # Pre-allocate the C string array for ["hello", "world"]
    c_strs = (ctypes.c_char_p * 2)(b"hello", b"world")
    out_str = ctypes.c_char_p()

    def bench_string():
        ret = lib.GoJoinStrings(c_strs, ctypes.c_int(2), ctypes.byref(out_str))
        if ret != 0:
            raise RuntimeError("GoJoinStrings failed")
        result = out_str.value.decode("utf-8")
        lib.GoFreeString(out_str)
        if result != "hello,world":
            raise RuntimeError(f"JoinStrings = {result!r}, want 'hello,world'")

    if _should_run(scenario_filter, "string_echo", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "string_echo", None, WARMUP, ITERATIONS, bench_string
        ))

    # --- Scenario 4: Array echo (varying sizes) ---
    for size in [10, 100, 1000, 10000]:
        if not _should_run(scenario_filter, "array_echo", size):
            continue
        selected_count += 1
        data = bytes(i % 256 for i in range(size))
        out_ptr = ctypes.c_void_p()
        out_len = ctypes.c_int()

        def bench_array(d=data, sz=size):
            ret = lib.GoEchoBytes(d, ctypes.c_int(sz),
                                  ctypes.byref(out_ptr), ctypes.byref(out_len))
            if ret != 0:
                raise RuntimeError("GoEchoBytes failed")
            if out_len.value != sz:
                raise RuntimeError(
                    f"EchoBytes({sz}): got len {out_len.value}, want {sz}"
                )
            lib.GoFreeBytes(out_ptr)

        benchmarks.append(run_benchmark(
            "array_echo", size, WARMUP, ITERATIONS, bench_array
        ))

    # --- Scenario 5: Object create + method call ---
    handle = ctypes.c_uint64()
    name_out = ctypes.c_char_p()

    def bench_object():
        ret = lib.GoNewTestMap(ctypes.byref(handle))
        if ret != 0:
            raise RuntimeError("GoNewTestMap failed")

        ret = lib.GoTestMapGetName(handle, ctypes.byref(name_out))
        if ret != 0:
            raise RuntimeError("GoTestMapGetName failed")

        name = name_out.value.decode("utf-8")
        lib.GoFreeString(name_out)
        lib.GoFreeHandle(handle)

        if name != "name1":
            raise RuntimeError(f"TestMap.Name = {name!r}, want 'name1'")

    if _should_run(scenario_filter, "object_method", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "object_method", None, WARMUP, ITERATIONS, bench_object
        ))

    # --- Scenario 6: Callback invocation ---
    @AddCallbackType
    def c_adder(a, b):
        return a + b

    cb_result = ctypes.c_int64()

    def bench_callback():
        ret = lib.GoCallCallbackAdd(c_adder, ctypes.byref(cb_result))
        if ret != 0:
            raise RuntimeError("GoCallCallbackAdd failed")
        if cb_result.value != 3:
            raise RuntimeError(f"CallCallbackAdd: got {cb_result.value}, want 3")

    if _should_run(scenario_filter, "callback", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "callback", None, WARMUP, ITERATIONS, bench_callback
        ))

    # --- Scenario 7: Error propagation ---
    err_msg = ctypes.c_char_p()

    def bench_error():
        ret = lib.GoReturnsAnError(ctypes.byref(err_msg))
        if ret == 0:
            raise RuntimeError("GoReturnsAnError did not return error")
        # Free the error string
        lib.GoFreeString(err_msg)

    if _should_run(scenario_filter, "error_propagation", None):
        selected_count += 1
        benchmarks.append(run_benchmark(
            "error_propagation", None, WARMUP, ITERATIONS, bench_error
        ))

    # --- Scenario: Dynamic any echo (mixed payload) ---
    any_echo_size = 100
    if _should_run(scenario_filter, "any_echo", any_echo_size):
        selected_count += 1
        pattern = ["1", "\"two\"", "3.0"]
        payload_json = "[" + ",".join(pattern[i % len(pattern)] for i in range(any_echo_size)) + "]"
        payload_bytes = payload_json.encode("utf-8")
        out_any_json = ctypes.c_char_p()

        def bench_any_echo(data=payload_bytes, expected=payload_json):
            ret = lib.GoAnyEchoJSON(data, ctypes.byref(out_any_json))
            if ret != 0:
                raise RuntimeError("GoAnyEchoJSON failed")
            echoed = out_any_json.value.decode("utf-8")
            lib.GoFreeString(out_any_json)
            if echoed != expected:
                raise RuntimeError("GoAnyEchoJSON returned mismatched payload")

        benchmarks.append(run_benchmark(
            "any_echo", any_echo_size, WARMUP, ITERATIONS, bench_any_echo
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
