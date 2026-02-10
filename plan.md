# MetaFFI Cross-Language Testing & Benchmarking Framework

This document describes the cross-language testing, performance benchmarking, and code complexity analysis framework for the MetaFFI PhD thesis. It covers what each test does, how to run it, where results are stored, what metrics are collected, and all dependencies.

---

## Quick Start

```powershell
# Run all tests (skips tests with existing results)
python tests/run_all_tests.py

# Re-run everything from scratch
python tests/run_all_tests.py --all

# Run only Go-as-host tests
python tests/run_all_tests.py --host go

# Run only one pair
python tests/run_all_tests.py --pair go:python3

# Custom iteration count
python tests/run_all_tests.py --iterations 50000 --warmup 200

# Consolidate results (run after tests complete)
python tests/consolidate_results.py

# Generate thesis tables
python tests/generate_tables.py

# Run complexity analysis
python tests/analyze_complexity.py
```

---

## Test Matrix (18 Triples)

Each of the 6 directional language pairs is tested with 3 interop mechanisms:

| Host -> Guest | MetaFFI | Native Direct | gRPC Baseline |
|---------------|---------|---------------|---------------|
| Go -> Python3 | `go/call_python3/` | `go/without_metaffi/call_python3_cpython/` (cgo+CPython) | `go/without_metaffi/call_python3_grpc/` |
| Go -> Java | `go/call_java/` | `go/without_metaffi/call_java_jni/` (cgo+JNI) | `go/without_metaffi/call_java_grpc/` |
| Python3 -> Go | `python3/call_go/` | `python3/without_metaffi/call_go_ctypes/` (ctypes) | `python3/without_metaffi/call_go_grpc/` |
| Python3 -> Java | `python3/call_java/` | `python3/without_metaffi/call_java_jpype/` (JPype) | `python3/without_metaffi/call_java_grpc/` |
| Java -> Go | `java/call_go/` | `java/without_metaffi/call_go_jni/` (JNI+cgo) | `java/without_metaffi/call_go_grpc/` |
| Java -> Python3 | `java/call_python3/` | `java/without_metaffi/call_python3_jep/` (Jep) | `java/without_metaffi/call_python3_grpc/` |

**Total**: 6 MetaFFI + 6 native-direct + 6 gRPC = **18 implementations**

---

## What Each Test Does

### MetaFFI Tests (6 implementations)

Each MetaFFI test directory contains **correctness tests** and **performance benchmarks**.

**Correctness tests** exercise every entity in the guest module:
- Functions: `hello_world()`, `div_integers()`, `join_strings()`, `returns_an_error()`, etc.
- Callbacks: `call_callback_add()`, `return_callback_add()`
- Objects/Classes: `SomeClass` constructor + all methods, `TestMap.Set/Get/Contains`
- Primitives: int8..uint64, float32/64, bool, string
- Arrays: 1D, 2D, 3D, ragged, string arrays
- Error handling: exception propagation, error return values
- Globals/State: module-level state get/set

**Performance benchmarks** run the 7 representative scenarios (see below).

| MetaFFI Test | Correctness File | Benchmark File | Result JSON |
|-------------|------------------|----------------|-------------|
| Go -> Python3 | `go/call_python3/correctness_test.go` | `go/call_python3/benchmark_test.go` | `go_to_python3_metaffi.json` |
| Go -> Java | `go/call_java/correctness_test.go` | `go/call_java/benchmark_test.go` | `go_to_java_metaffi.json` |
| Python3 -> Go | `python3/call_go/test_correctness.py` | `python3/call_go/test_benchmark.py` | `python3_to_go_metaffi.json` |
| Python3 -> Java | `python3/call_java/test_correctness.py` | `python3/call_java/test_benchmark.py` | `python3_to_java_metaffi.json` |
| Java -> Go | `java/call_go/src/test/java/TestCorrectness.java` | `java/call_go/src/test/java/TestBenchmark.java` | `java_to_go_metaffi.json` |
| Java -> Python3 | `java/call_python3/src/test/java/TestCorrectness.java` | `java/call_python3/src/test/java/TestBenchmark.java` | `java_to_python3_metaffi.json` |

### Native Direct Tests (6 implementations)

Each native test implements only the 7 performance benchmark scenarios using the language's native interop mechanism (no MetaFFI). No correctness tests.

| Native Test | Mechanism | Benchmark File | Result JSON |
|------------|-----------|----------------|-------------|
| Go -> Python3 | cgo + CPython C API | `go/without_metaffi/call_python3_cpython/benchmark_test.go` + `bridge.go` | `go_to_python3_cpython.json` |
| Go -> Java | cgo + JNI | `go/without_metaffi/call_java_jni/benchmark_test.go` + `bridge.go` | `go_to_java_jni.json` |
| Python3 -> Go | ctypes + cgo .dll | `python3/without_metaffi/call_go_ctypes/benchmark.py` + `go_bridge/bridge.go` | `python3_to_go_ctypes.json` |
| Python3 -> Java | JPype | `python3/without_metaffi/call_java_jpype/benchmark.py` | `python3_to_java_jpype.json` |
| Java -> Go | JNI + cgo .dll | `java/without_metaffi/call_go_jni/src/test/java/BenchmarkTest.java` + `go_bridge/` | `java_to_go_jni.json` |
| Java -> Python3 | Jep (embedded CPython) | `java/without_metaffi/call_python3_jep/src/test/java/BenchmarkTest.java` | `java_to_python3_jep.json` |

### gRPC Baseline Tests (6 implementations)

Each gRPC test runs the guest module as a localhost gRPC server and the host calls it as a client. Implements the 7 benchmark scenarios. No correctness tests.

All gRPC pairs share the same architecture:
1. `benchmark.proto` defines 7 RPCs (callback uses bidirectional streaming since functions can't be passed over gRPC)
2. Server process in guest language wraps the guest module
3. Client in host language connects via `localhost:<port>`
4. Server process is started as a subprocess, prints `READY:<port>` to stdout
5. Client runs warmup + measured iterations, writes JSON results
6. Server process is killed on test teardown

| gRPC Test | Client File | Server | Result JSON |
|-----------|-------------|--------|-------------|
| Go -> Python3 | `go/without_metaffi/call_python3_grpc/benchmark_test.go` | `server/server.py` | `go_to_python3_grpc.json` |
| Go -> Java | `go/without_metaffi/call_java_grpc/benchmark_test.go` | `server/.../BenchmarkServer.java` | `go_to_java_grpc.json` |
| Python3 -> Go | `python3/without_metaffi/call_go_grpc/benchmark.py` | `server/server.go` | `python3_to_go_grpc.json` |
| Python3 -> Java | `python3/without_metaffi/call_java_grpc/benchmark.py` | reuses Java server from `go/without_metaffi/call_java_grpc/server/` | `python3_to_java_grpc.json` |
| Java -> Go | `java/without_metaffi/call_go_grpc/src/test/java/BenchmarkTest.java` | reuses Go server from `python3/without_metaffi/call_go_grpc/server/` | `java_to_go_grpc.json` |
| Java -> Python3 | `java/without_metaffi/call_python3_grpc/src/test/java/BenchmarkTest.java` | reuses Python server from `go/without_metaffi/call_python3_grpc/server/` | `java_to_python3_grpc.json` |

---

## Performance Benchmark Scenarios

All 18 implementations benchmark the same 7 scenarios (10 benchmarks total including array size variants):

| # | Scenario | Input | Output | Purpose |
|---|----------|-------|--------|---------|
| 1 | `void_call` | none | none | Base call overhead |
| 2 | `primitive_echo` | int64 | int64 | Single primitive marshaling |
| 3 | `string_echo` | string | string | String marshaling |
| 4 | `array_sum_10` | int64[10] | int64 | Array marshaling (small) |
| 5 | `array_sum_100` | int64[100] | int64 | Array marshaling (medium) |
| 6 | `array_sum_1000` | int64[1000] | int64 | Array marshaling (large) |
| 7 | `array_sum_10000` | int64[10000] | int64 | Array marshaling (very large) |
| 8 | `object_method` | constructor + method | handle, string | Object/handle passing |
| 9 | `callback` | callable(int,int)->int | int64 | Bidirectional crossing |
| 10 | `error_propagation` | none | error | Error path overhead |

Some implementations use `array_echo` (roundtrip a byte/int array) instead of `array_sum` depending on the guest module API.

**Guest module entities used by benchmarks:**

| Scenario | Python3 guest | Java guest | Go guest |
|----------|--------------|------------|----------|
| void_call | `wait_a_bit(0)` | `CoreFunctions.waitABit(0)` | `WaitABit(0)` |
| primitive_echo | `div_integers(x,y)` | `CoreFunctions.divIntegers(x,y)` | `DivIntegers(x,y)` |
| string_echo | `join_strings(arr)` | `CoreFunctions.joinStrings(arr)` | `JoinStrings(arr)` |
| array_sum | `sum_ragged_array(arr)` | `ArrayFunctions.sumRaggedArray(arr)` | `EchoBytes(arr)` / `SumRaggedArray(arr)` |
| object_method | `SomeClass(name).print()` | `new SomeClass(name).print()` | `NewSomeClass(name).Print()` |
| callback | `call_callback_add(fn)` | `CoreFunctions.callCallbackAdd(fn)` | `CallCallbackAdd(fn)` |
| error_propagation | `returns_an_error()` | `CoreFunctions.returnsAnError()` | `ReturnsAnError()` |

---

## Metrics Collected

### Per-Benchmark Metrics

Each benchmark scenario produces these statistics (computed after IQR-based outlier removal):

| Metric | Description |
|--------|-------------|
| `mean_ns` | Arithmetic mean of measured iterations (nanoseconds) |
| `median_ns` | Median (50th percentile) |
| `p95_ns` | 95th percentile |
| `p99_ns` | 99th percentile |
| `stddev_ns` | Standard deviation |
| `ci95_ns` | 95% confidence interval [low, high] |

All timing in **nanoseconds** (int64).

### Statistical Methodology

- **Warmup**: First 100 iterations discarded (configurable via `METAFFI_TEST_WARMUP`). Critical for JVM JIT compilation.
- **Sample size**: 10,000 measured iterations per scenario (configurable via `METAFFI_TEST_ITERATIONS`).
- **Outlier detection**: IQR-based. Values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR are excluded from statistical computation.
- **Timer overhead**: Measured at startup (10K samples of empty timing loop). Reported in result metadata as `timer_overhead_ns`.

### High-Resolution Timing

| Language | Timer API | Resolution |
|----------|-----------|------------|
| Go | `time.Now()` / `time.Since()` | ~1 ns (monotonic) |
| Python3 | `time.perf_counter_ns()` | ~100 ns (best available) |
| Java | `System.nanoTime()` | ~1 ns (monotonic) |

### Initialization Timing (Separate)

Reported separately from per-call metrics:
- MetaFFI: `load_runtime_plugin_ns` + `load_module_ns`
- Native: equivalent init (JVM creation, Py_Initialize, DLL loading, gRPC channel)

### Code Complexity Metrics

Collected by `analyze_complexity.py`:

| Metric | Tool | Description |
|--------|------|-------------|
| SLOC | cloc | Source lines of code (non-blank, non-comment) |
| Benchmark-only SLOC | cloc + classification | SLOC excluding MetaFFI correctness test files |
| File count | filesystem | Number of source files |
| Language count | cloc | Programming languages used |
| Cyclomatic complexity | lizard | McCabe complexity per function (max reported) |

---

## Result File Schema

Each test produces a JSON file at `tests/results/<host>_to_<guest>_<mechanism>.json`:

```json
{
  "metadata": {
    "host": "go",
    "guest": "python3",
    "mechanism": "metaffi",
    "timestamp": "2026-02-10T14:30:00Z",
    "environment": {
      "os": "windows",
      "arch": "amd64",
      "go_version": "1.22",
      "python_version": "3.12",
      "java_version": "22"
    },
    "config": {
      "warmup_iterations": 100,
      "measured_iterations": 10000,
      "timer_overhead_ns": 25
    }
  },
  "correctness": {
    "status": "PASS",
    "total": 47,
    "passed": 47,
    "failed": 0,
    "xfailed": 0
  },
  "initialization": {
    "load_runtime_plugin_ns": 123456,
    "load_module_ns": 78901
  },
  "benchmarks": [
    {
      "scenario": "primitive_echo",
      "data_size": null,
      "status": "PASS",
      "raw_iterations_ns": [1234, 1201, ...],
      "phases": {
        "total": {
          "mean_ns": 1200,
          "median_ns": 1180,
          "p95_ns": 1450,
          "p99_ns": 1600,
          "stddev_ns": 80,
          "ci95_ns": [1190, 1210]
        }
      }
    },
    {
      "scenario": "array_sum",
      "data_size": 1000,
      "status": "PASS",
      "..."
    }
  ]
}
```

For native/gRPC tests, `correctness` is `null` (no correctness tests).

---

## How to Run Each Test Individually

### Go Host Tests

```powershell
# Set required env vars
$env:METAFFI_HOME = "c:\src\github.com\MetaFFI"
$env:METAFFI_SOURCE_ROOT = "c:\src\github.com\MetaFFI"
$env:METAFFI_TEST_ITERATIONS = "10000"
$env:METAFFI_TEST_WARMUP = "100"

# Go -> Python3 MetaFFI
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\go_to_python3_metaffi.json"
cd c:\src\github.com\MetaFFI\tests\go\call_python3
go test -v -count=1 -timeout=600s ./...

# Go -> Java MetaFFI
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\go_to_java_metaffi.json"
cd c:\src\github.com\MetaFFI\tests\go\call_java
go test -v -count=1 -timeout=600s ./...

# Go -> Python3 cgo+CPython (native)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\go_to_python3_cpython.json"
cd c:\src\github.com\MetaFFI\tests\go\without_metaffi\call_python3_cpython
go test -v -count=1 -timeout=600s ./...

# Go -> Java cgo+JNI (native)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\go_to_java_jni.json"
cd c:\src\github.com\MetaFFI\tests\go\without_metaffi\call_java_jni
go test -v -count=1 -timeout=600s ./...

# Go -> Python3 gRPC
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\go_to_python3_grpc.json"
cd c:\src\github.com\MetaFFI\tests\go\without_metaffi\call_python3_grpc
go test -v -count=1 -timeout=600s ./...

# Go -> Java gRPC
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\go_to_java_grpc.json"
cd c:\src\github.com\MetaFFI\tests\go\without_metaffi\call_java_grpc
go test -v -count=1 -timeout=600s ./...
```

### Python3 Host Tests

```powershell
$env:METAFFI_HOME = "c:\src\github.com\MetaFFI"
$env:METAFFI_SOURCE_ROOT = "c:\src\github.com\MetaFFI"
$env:METAFFI_TEST_ITERATIONS = "10000"
$env:METAFFI_TEST_WARMUP = "100"

# Python3 -> Go MetaFFI (uses pytest)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\python3_to_go_metaffi.json"
python -m pytest -v --tb=short c:\src\github.com\MetaFFI\tests\python3\call_go

# Python3 -> Java MetaFFI (uses pytest)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\python3_to_java_metaffi.json"
python -m pytest -v --tb=short c:\src\github.com\MetaFFI\tests\python3\call_java

# Python3 -> Go ctypes (standalone script)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\python3_to_go_ctypes.json"
python c:\src\github.com\MetaFFI\tests\python3\without_metaffi\call_go_ctypes\benchmark.py

# Python3 -> Java JPype (standalone script)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\python3_to_java_jpype.json"
python c:\src\github.com\MetaFFI\tests\python3\without_metaffi\call_java_jpype\benchmark.py

# Python3 -> Go gRPC (standalone script)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\python3_to_go_grpc.json"
python c:\src\github.com\MetaFFI\tests\python3\without_metaffi\call_go_grpc\benchmark.py

# Python3 -> Java gRPC (standalone script)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\python3_to_java_grpc.json"
python c:\src\github.com\MetaFFI\tests\python3\without_metaffi\call_java_grpc\benchmark.py
```

### Java Host Tests

```powershell
$env:METAFFI_HOME = "c:\src\github.com\MetaFFI"
$env:METAFFI_SOURCE_ROOT = "c:\src\github.com\MetaFFI"
$env:METAFFI_TEST_ITERATIONS = "10000"
$env:METAFFI_TEST_WARMUP = "100"
# Maven path (if not on PATH)
$MVN = "C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd"

# Java -> Go MetaFFI
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\java_to_go_metaffi.json"
cd c:\src\github.com\MetaFFI\tests\java\call_go
& $MVN test "-Dtest=TestCorrectness,TestBenchmark" -pl .

# Java -> Python3 MetaFFI
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\java_to_python3_metaffi.json"
cd c:\src\github.com\MetaFFI\tests\java\call_python3
& $MVN test "-Dtest=TestCorrectness,TestBenchmark" -pl .

# Java -> Go JNI+cgo (native)
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\java_to_go_jni.json"
cd c:\src\github.com\MetaFFI\tests\java\without_metaffi\call_go_jni
& $MVN test "-Dtest=BenchmarkTest" -pl .

# Java -> Python3 Jep (native) -- requires JEP_HOME
$env:JEP_HOME = (python -c "import importlib.util; spec = importlib.util.find_spec('jep'); print(spec.submodule_search_locations[0])")
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\java_to_python3_jep.json"
cd c:\src\github.com\MetaFFI\tests\java\without_metaffi\call_python3_jep
& $MVN test "-Dtest=BenchmarkTest" -pl .

# Java -> Go gRPC
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\java_to_go_grpc.json"
cd c:\src\github.com\MetaFFI\tests\java\without_metaffi\call_go_grpc
& $MVN test "-Dtest=BenchmarkTest" -pl .

# Java -> Python3 gRPC
$env:METAFFI_TEST_RESULTS_FILE = "c:\src\github.com\MetaFFI\tests\results\java_to_python3_grpc.json"
cd c:\src\github.com\MetaFFI\tests\java\without_metaffi\call_python3_grpc
& $MVN test "-Dtest=BenchmarkTest" -pl .
```

---

## Output Files

| File | Description |
|------|-------------|
| `results/<host>_to_<guest>_<mechanism>.json` | Per-triple raw benchmark results (18 files when complete) |
| `results/consolidated.json` | Merged results with comparison tables, missing/failed tracking |
| `results/complexity.json` | SLOC and cyclomatic complexity analysis for all 18 implementations |
| `results/tables.md` | Human-readable markdown tables for thesis inclusion |

---

## Infrastructure Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `run_all_tests.py` | Run all 18 tests, skip existing, report failures | `python run_all_tests.py [--all]` |
| `consolidate_results.py` | Merge per-triple JSON files into `consolidated.json` | `python consolidate_results.py` |
| `generate_tables.py` | Generate markdown tables from consolidated + complexity data | `python generate_tables.py` |
| `analyze_complexity.py` | Compute SLOC/CC for all 18 implementations | `python analyze_complexity.py` |
| `run_tests.py` | Legacy orchestration script (superseded by `run_all_tests.py`) | `python run_tests.py` |

---

## Dependencies

### System Requirements

| Dependency | Purpose | Location / Install |
|-----------|---------|-------------------|
| Go >= 1.21 | Go host tests, cgo bridge compilation | On PATH |
| Python >= 3.10 | Python3 host tests, analysis scripts | On PATH as `python` |
| Java (OpenJDK) >= 11 | Java host tests, JVM guest | `JAVA_HOME` env var |
| Maven >= 3.9 | Java test execution | `C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd` |
| protoc | gRPC stub generation (already generated) | `C:\Users\green\AppData\Local\Microsoft\WinGet\Packages\Google.Protobuf_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\protoc.exe` |
| MetaFFI | Framework under test | `METAFFI_HOME` env var |

### Environment Variables

| Variable | Required | Value |
|----------|----------|-------|
| `METAFFI_HOME` | Yes | MetaFFI installation root (e.g., `c:\src\github.com\MetaFFI`) |
| `METAFFI_SOURCE_ROOT` | Yes | MetaFFI source root (same as above for dev) |
| `JAVA_HOME` | Yes | JDK installation (e.g., `C:\Program Files\OpenJDK\jdk-22.0.2`) |
| `METAFFI_TEST_ITERATIONS` | No | Override default 10000 iterations |
| `METAFFI_TEST_WARMUP` | No | Override default 100 warmup iterations |
| `METAFFI_TEST_RESULTS_FILE` | No | Override output JSON path |
| `METAFFI_TEST_MODE` | No | `all`, `correctness`, or `benchmarks` |
| `JEP_HOME` | For Jep | Path to Jep package (auto-detected if pip-installed) |

### Python Packages

| Package | Purpose | Install |
|---------|---------|---------|
| pytest | Python MetaFFI test runner | `pip install pytest` |
| grpcio + protobuf | gRPC Python clients/servers | `pip install grpcio protobuf` |
| jpype1 | Python -> Java native baseline | `pip install jpype1` |
| jep | Java -> Python3 native baseline | `pip install jep` |
| cloc | SLOC counting (analysis) | `pip install cloc` or `winget install cloc` |
| lizard | Cyclomatic complexity (analysis) | `pip install lizard` |
| radon | Python CC (analysis, optional) | `pip install radon` |

### Go Modules

Go test directories contain their own `go.mod` files with dependencies. Key ones:
- `google.golang.org/grpc` + `google.golang.org/protobuf` (gRPC tests)
- MetaFFI SDK via `replace` directives pointing to local `sdk/api/go/`

### Java / Maven

Java tests use Maven (`pom.xml` in each directory). Dependencies managed via Maven:
- JUnit 4.13.1 (test framework)
- gRPC 1.62.2 + Protobuf 3.25.3 (gRPC tests -- NOT protobuf 4.x)
- MetaFFI API via system-scoped dependency at `$METAFFI_HOME/sdk/api/jvm/metaffi.api.jar`
- Jep via system-scoped dependency (Jep test only)

---

## Guest Modules

All tests call entities from pre-existing guest modules:

| Language | Source | Compiled |
|----------|--------|----------|
| Go | `sdk/test_modules/guest_modules/go/*.go` | `sdk/test_modules/guest_modules/go/test_bin/guest_MetaFFIGuest.dll` |
| Java | `sdk/test_modules/guest_modules/java/src/guest/*.java` | `sdk/test_modules/guest_modules/java/test_bin/guest_java.jar` |
| Python3 | `sdk/test_modules/guest_modules/python3/module/*.py` | (interpreted, no compilation) |

Full entity specification: `sdk/test_modules/guest_modules/guest_modules_doc.md`

---

## Known Issues

### [BLOCKING] cgo Crashes on Windows (3 tests)

All Go-host tests using cgo to invoke foreign runtimes crash with `Exception 0xc0000005` (access violation):

| Test | Crash Location | Missing Result |
|------|---------------|----------------|
| Go -> Java MetaFFI | `xllr_load_runtime_plugin("jvm")` | `go_to_java_metaffi.json` |
| Go -> Java cgo+JNI | `jvm_initialize()` (JNI_CreateJavaVM) | `go_to_java_jni.json` |
| Go -> Python3 cgo+CPython | `bench_void_call()` (CPython C API) | `go_to_python3_cpython.json` |

Not affected: gRPC tests (no cgo), Go -> Python3 MetaFFI (xllr.python3.dll works).

### [KNOWN] xcall_no_params_ret Bug (Python3 Guest)

Calls to Python3 guest entities with no input params but return values fail: `Index 0 out of bounds (CDTS size: 0)`.

Affected:
- Go -> Python3 MetaFFI: `object_method` benchmark FAIL
- Java -> Python3 MetaFFI: `object_method` benchmark FAIL, 25 correctness tests xfailed

### [KNOWN] Type Mapping Mismatches

- Python3 -> Go: 14 xfailed tests (Go `int` vs `int64`, 2D byte arrays, named types, generics, varargs)
- Python3 -> Java: 19 xfailed tests + `callback` benchmark FAIL
- Java -> Go: 2 xfailed tests (Go named function type `StringTransformer`)

### Result File Status (15 of 18)

| Result File | Status |
|-------------|--------|
| `go_to_python3_metaffi.json` | Generated (object_method FAIL, rest PASS) |
| `go_to_python3_grpc.json` | Generated (all PASS) |
| `go_to_java_grpc.json` | Generated (all PASS) |
| `go_to_java_metaffi.json` | **BLOCKED** (cgo JVM crash) |
| `go_to_python3_cpython.json` | **BLOCKED** (cgo CPython crash) |
| `go_to_java_jni.json` | **BLOCKED** (cgo JNI crash) |
| All 6 Python3-host files | Generated |
| All 6 Java-host files | Generated |

---

## Technical Reference

### MetaFFI Runtime Names

| Language | Runtime Name | Plugin DLL |
|----------|-------------|------------|
| Python3 | `python3` | `xllr.python3.dll` |
| Java/JVM | `jvm` | `xllr.jvm.dll` |
| Go | `go` | `xllr.go.dll` |

### Entity Path Format

Entity paths are comma-separated key=value pairs (see `sdk/idl_entities/entity_path_specs.json`):

**Python3**: `callable=function_name` | `callable=Class.method,instance_required` | `attribute=name,getter`

**Java**: `class=pkg.Class,callable=method` | `class=pkg.Class,callable=<init>` | `class=pkg.Class,field=name,getter,instance_required`

**Go**: `callable=FuncName` | `callable=Struct.Method` | `callable=Struct.GetField` / `callable=Struct.SetField`

### Build Environment Notes

- `JAVA_HOME` has spaces -- use 8.3 short path for cgo: `C:\PROGRA~1\OpenJDK\JDK-22~1.2`
- Maven not on PATH: `C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd`
- protoc not on PATH: `C:\Users\green\AppData\Local\Microsoft\WinGet\Packages\Google.Protobuf_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\protoc.exe`
- Java gRPC: use grpc 1.62.2 + protobuf 3.25.3 (NOT 4.x -- version mismatch with grpc-java)
- cgo: `import "C"` not supported in `_test.go` files -- bridge code goes in separate `.go` files
- cgo: only expands `${SRCDIR}` in `#cgo` directives, not other env vars

---

## Directory Structure

```
tests/
  plan.md                          # This document
  README.md                        # Brief overview
  run_all_tests.py                 # Master test runner (skip/rerun/report)
  run_tests.py                     # Legacy orchestration script
  consolidate_results.py           # Merge results into consolidated.json
  generate_tables.py               # Generate thesis tables from results
  analyze_complexity.py            # SLOC + cyclomatic complexity analysis
  results/                         # All output files
    <host>_to_<guest>_<mech>.json  # Per-triple results (18 files)
    consolidated.json              # Merged cross-pair comparison
    complexity.json                # Code complexity analysis
    tables.md                      # Human-readable comparison tables
  go/
    call_python3/                  # MetaFFI: Go -> Python3
    call_java/                     # MetaFFI: Go -> Java
    without_metaffi/
      call_python3_cpython/        # Native: cgo + CPython C API
      call_python3_grpc/           # gRPC baseline
      call_java_jni/               # Native: cgo + JNI
      call_java_grpc/              # gRPC baseline
  python3/
    call_go/                       # MetaFFI: Python3 -> Go
    call_java/                     # MetaFFI: Python3 -> Java
    without_metaffi/
      call_go_ctypes/              # Native: ctypes + cgo .dll
      call_go_grpc/                # gRPC baseline
      call_java_jpype/             # Native: JPype
      call_java_grpc/              # gRPC baseline
  java/
    call_go/                       # MetaFFI: Java -> Go
    call_python3/                  # MetaFFI: Java -> Python3
    without_metaffi/
      call_go_jni/                 # Native: JNI + cgo .dll
      call_go_grpc/                # gRPC baseline
      call_python3_jep/            # Native: Jep
      call_python3_grpc/           # gRPC baseline
```

---

## Fail-Fast Policy

Every test and benchmark fails loudly on unexpected conditions:
- No silent fallbacks or default values
- No swallowed errors -- all exceptions propagate
- Strict assertions with exact expected values
- Benchmark aborts if an iteration returns incorrect results
- No graceful degradation if a runtime fails to initialize
- Rationale: hidden fallbacks can silently pollute data, invalidating the thesis experiment
