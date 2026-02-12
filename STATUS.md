# MetaFFI Test Framework - Current Status

Last updated: 2026-02-11

See `tests/plan.md` for full project documentation (test matrix, schemas, how to run, dependencies, etc.).

---

## Overall Status

- **18 of 18** result files generated (all test pairs complete)
- **176 benchmarks passed**, **4 failed**
- **Phases 1-4 complete** (Go, Python3, Java as host - all MetaFFI + native + gRPC)
- **Phase 5** (Analysis & reporting) partially done: `consolidate_results.py`, `generate_tables.py`, `analyze_complexity.py` all working

Run `python tests/consolidate_results.py` to regenerate `results/consolidated.json` and `results/tables.md`.

---

## What Was Just Fixed (VEH/SEH)

Go's Vectored Exception Handler (VEH) intercepts JVM's internal SEH exceptions (null-check probes), crashing any cgo->JVM call. This blocked 3 Go-host tests.

**Fix**: Run `JNI_CreateJavaVM` and `load_entity` on dedicated Windows threads via `CreateThread`. Go's VEH returns `EXCEPTION_CONTINUE_SEARCH` on non-Go threads, letting JVM's SEH work.

**Files modified in the SDK** (these are changes to the MetaFFI SDK itself, not just tests):
- `sdk/runtime_manager/jvm/jvm.cpp` - `JNI_CreateJavaVM` wrapped in CreateThread (lines ~30-55 for struct/thread proc in anonymous namespace, lines ~710-725 for the modified `try_create_vm` lambda)
- `lang-plugin-jvm/runtime/jvm_runtime.cpp` - `load_entity` refactored: original body renamed to `load_entity_impl`, new `load_entity` dispatches via CreateThread on Windows (lines ~1900-1940 for struct/thread proc/wrapper, `load_entity_impl` follows)

**Files modified in tests** (these are test infrastructure changes):
- `tests/go/without_metaffi/call_java_jni/bridge.go` - Dynamic JVM loading via LoadLibraryExW + CreateThread for JVM init + `ensure_jvm_thread()` for subtest thread attachment
- `tests/go/without_metaffi/call_java_jni/benchmark_test.go` - `ensureThread(t)` at start of each subtest, removed `JVMDestroy()` (hangs)
- `tests/go/without_metaffi/call_python3_cpython/bridge.go` - Added `PySaveThread()`, `PyEnsureGIL()`, `PyReleaseGIL()` wrappers
- `tests/go/without_metaffi/call_python3_cpython/benchmark_test.go` - GIL release before `m.Run()`, `ensureThread(t)` with `t.Cleanup` for GIL release per subtest

**SDK DLL must be rebuilt after changes**: `cmake --build cmake-build-debug --config Debug --target xllr.jvm` then copy `cmake-build-debug/lang-plugin-jvm/runtime/xllr.jvm.dll` to `output/windows/x64/Debug/jvm/xllr.jvm.dll`.

**Risk**: If `xcall` operations trigger JVM SEH in the future (e.g., during GC safepoints), the same CreateThread pattern or a persistent worker thread would be needed. Currently 80,000+ xcall invocations work without issues.

---

## Open Issues

### Issue 1: "0 ns" values for Go-host native benchmarks (JNI + CPython)

**Problem**: Native JNI and CPython calls complete faster than Go's timer resolution (~100ns on Windows). Out of 10,000 raw_iterations_ns samples, almost all are `0`. After IQR outlier removal, the few nonzero values get discarded as outliers, giving mean=0.

**Affected files**: `results/go_to_java_jni.json` (all 10 scenarios), `results/go_to_python3_cpython.json` (all 10 scenarios). Also `results/go_to_java_metaffi.json` for faster scenarios (void_call, primitive_echo, string_echo, error_propagation show 0 ns).

**Evidence**: void_call has 2/10000 nonzero samples (JNI), 1/10000 (CPython). Even array_sum_10000 only has 260/10000 (JNI) and 2442/10000 (CPython) nonzero.

**Impact on tables**: The comparison table in `results/tables.md` shows "0 ns" for all JNI and CPython columns, making cross-mechanism comparison impossible for Go-host pairs.

**Fix options**:
1. **Batch measurement** (recommended): Change `runBenchmark` to run N calls per timing sample and divide. E.g., time 1000 calls as one sample, report per-call = elapsed/1000. Requires modifying `benchmark_test.go` + each `BenchXxx()` function in both `call_java_jni/` and `call_python3_cpython/`. Same approach needed for Go->Java MetaFFI's fast scenarios.
2. **Accept as-is**: "<100ns" is meaningful for the thesis (shows native overhead is negligible). Document in thesis that native calls are below timer resolution.

**How to reproduce**:
```powershell
cd C:\src\github.com\MetaFFI\tests\go\without_metaffi\call_java_jni
go test -v -run TestBenchmarkAll -count=1 -timeout 15m
# Check results: results/go_to_java_jni.json — raw_iterations_ns will be mostly 0
```

### Issue 2: Go->Java MetaFFI `callback` benchmark FAIL

**Error**: `java.lang.NoSuchMethodException: guest.CoreFunctions.callCallbackAdd(metaffi.api.accessor.Caller)`

**Diagnosis**: MetaFFI wraps the Go callback as a `metaffi.api.accessor.Caller` object, but `callCallbackAdd(BiFunction<Integer,Integer,Integer>)` in Java expects a functional interface. JVM method resolution fails because Caller doesn't match BiFunction.

**Location**: `tests/go/call_java/benchmark_test.go` lines 349-367 (callback scenario), `tests/go/call_java/correctness_test.go` also has callback tests.

**How to reproduce**:
```powershell
cd C:\src\github.com\MetaFFI\tests\go\call_java
go test -v -run TestBenchmarkAll/callback -count=1 -timeout 2m
```

### Issue 3: Python3->Java MetaFFI `callback` benchmark FAIL

**Error**: `Failed to load entity` for `class=guest.CoreFunctions,callable=callCallbackAdd`

**Diagnosis**: Same root cause as Issue 2 (callback parameter type mismatch during entity loading from Python3 host).

**How to reproduce**:
```powershell
cd C:\src\github.com\MetaFFI\tests\python3\call_java
python -m pytest -v -k "test_benchmark_callback" --tb=short
```

### Issue 4: `object_method` FAIL for Go->Python3 and Java->Python3 MetaFFI

**Error**: `xcall_no_params_ret bug: Index 0 out of bounds (CDTS size: 0)`

**Diagnosis**: Known MetaFFI SDK bug in `xcall_no_params_ret`. When calling `SomeClass.print()` (no params, returns string), the CDTS return buffer is allocated with size 0 instead of 1.

**How to reproduce**:
```powershell
# Go->Python3
cd C:\src\github.com\MetaFFI\tests\go\call_python3
go test -v -run TestBenchmarkAll/object_method -count=1 -timeout 2m

# Java->Python3
cd C:\src\github.com\MetaFFI\tests\java\call_python3
& "C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd" test "-Dtest=TestBenchmark#testObjectMethod" -pl .
```

---

## What's Next (Phase 5 Completion)

1. **Decide on Issue 1** (0 ns values): batch measurement vs. accept as-is
2. **Issues 2-4** are MetaFFI SDK bugs — decide whether to fix in SDK or document as known limitations
3. **Final run**: Execute `python tests/run_all_tests.py --all` for a clean full run once issues are resolved
4. **Generate final thesis tables**: `python tests/consolidate_results.py` then `python tests/generate_tables.py`
5. **Review complexity analysis**: `python tests/analyze_complexity.py` — verify SLOC/CC numbers are accurate

---

## Key File Locations

| File | Purpose |
|------|---------|
| `tests/plan.md` | Full project documentation, test matrix, schemas, how-to-run |
| `tests/results/tables.md` | Current comparison tables (regenerate with `consolidate_results.py`) |
| `tests/results/consolidated.json` | Machine-readable merged results |
| `tests/run_all_tests.py` | Master test runner |
| `tests/consolidate_results.py` | Merges per-triple JSONs, generates tables.md |
| `tests/analyze_complexity.py` | SLOC + cyclomatic complexity analysis |
| `tests/generate_tables.py` | Generates thesis tables from consolidated + complexity data |

## Build Environment Reminders

- Maven: `C:\ProgramData\chocolatey\lib\maven\apache-maven-3.9.12\bin\mvn.cmd`
- protoc: `C:\Users\green\AppData\Local\Microsoft\WinGet\Packages\Google.Protobuf_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\protoc.exe`
- JAVA_HOME 8.3 short path (for cgo): `C:\PROGRA~1\OpenJDK\JDK-22~1.2`
- Runtime names: `python3`, `jvm` (not "java"), `go`
- Java gRPC: use grpc 1.62.2 + protobuf 3.25.3 (NOT 4.x)
- `xllr.jvm.dll` build: `cmake --build cmake-build-debug --config Debug --target xllr.jvm`
