# MetaFFI Cross-Language Analysis

Correctness testing, performance profiling, and code complexity analysis of MetaFFI cross-language interop vs. native alternatives.

This project is part of a PhD thesis evaluating MetaFFI as a universal cross-language interoperability framework.

## What This Project Does

For every combination of **host language** (the caller) and **guest language** (the callee) among Go, Java, and Python3, this project:

1. **Correctness tests** -- calls every entity exposed by the guest module via MetaFFI and asserts the expected results.
2. **Performance benchmarks** -- measures call latency for 7 representative scenarios using three mechanisms:
   - **MetaFFI** (the framework under study)
   - **Native direct interop** (cgo+JNI, ctypes, JPype, Jep, cgo+CPython -- whichever is standard for the pair)
   - **gRPC** (universal baseline, all pairs)
3. **Code complexity analysis** -- compares SLOC, file count, language count, cyclomatic complexity, and API surface between MetaFFI and native implementations.

All results are written as machine-readable JSON files under `results/`.

## Fail-Fast Policy

**Every test and benchmark fails loudly on any unexpected condition.** No silent fallbacks, no swallowed errors, no retries. If a correctness test fails for a pair, benchmarks for that pair are skipped. This prevents polluted data in the analysis.

## Languages & Directions

| Host | Guest | MetaFFI | Native Direct | gRPC |
|------|-------|---------|---------------|------|
| Go | Python3 | `go/call_python3/` | `go/without_metaffi/call_python3_cpython/` | `go/without_metaffi/call_python3_grpc/` |
| Go | Java | `go/call_java/` | `go/without_metaffi/call_java_jni/` | `go/without_metaffi/call_java_grpc/` |
| Python3 | Go | `python3/call_go/` | `python3/without_metaffi/call_go_ctypes/` | `python3/without_metaffi/call_go_grpc/` |
| Python3 | Java | `python3/call_java/` | `python3/without_metaffi/call_java_jpype/` | `python3/without_metaffi/call_java_grpc/` |
| Java | Go | `java/call_go/` | `java/without_metaffi/call_go_jni/` | `java/without_metaffi/call_go_grpc/` |
| Java | Python3 | `java/call_python3/` | `java/without_metaffi/call_python3_jep/` | `java/without_metaffi/call_python3_grpc/` |

## Running

```bash
# Run everything (correctness + benchmarks for all pairs), then consolidate
python run_tests.py

# Run only Go-as-host tests
python run_tests.py --host go

# Run a specific pair
python run_tests.py --pair go:python3

# Correctness only (skip benchmarks)
python run_tests.py --correctness-only

# Benchmarks only (skip correctness)
python run_tests.py --benchmarks-only

# Override iteration count
python run_tests.py --iterations 50000

# Consolidate existing result files without re-running tests
python consolidate_results.py
```

### Prerequisites

- `METAFFI_HOME` environment variable set
- Go, Python3, Java installed and on PATH
- MetaFFI SDK built and installed
- Guest modules built (artifacts in `sdk/test_modules/guest_modules/*/test_bin/`)

## Output

Each (host, guest, mechanism) triple produces a JSON file in `results/`:

```
results/
  go_to_python3_metaffi.json
  go_to_python3_cpython.json
  go_to_python3_grpc.json
  ...
  consolidated.json        # All results merged
```

Each file contains:
- **metadata**: host, guest, mechanism, environment info, config
- **correctness**: pass/fail status per entity
- **initialization**: one-time load times (reported separately)
- **benchmarks**: per-scenario raw iteration timings + summary statistics (mean, median, p95, p99, stddev, 95% CI)

## Benchmark Scenarios

| # | Scenario | Purpose |
|---|----------|---------|
| 1 | Void call | Base call overhead |
| 2 | Primitive echo (int64) | Single primitive serialization |
| 3 | String echo | String marshaling |
| 4 | Array sum (sizes: 10, 100, 1K, 10K) | Array serialization scaling |
| 5 | Object create + method call | Object/handle passing |
| 6 | Callback invocation | Bidirectional crossing |
| 7 | Error propagation | Error path overhead |

## Timing

All measurements use high-resolution monotonic clocks in nanoseconds:
- Go: `time.Now()` / `time.Since()`
- Python3: `time.perf_counter_ns()`
- Java: `System.nanoTime()`

Both MetaFFI and native interop calls are instrumented with phase breakdowns (marshal/call/unmarshal).

## Project Structure

```
tests/
  README.md                          # This file
  plan.md                            # Detailed plan and methodology
  run_tests.py                       # Master orchestration script
  consolidate_results.py             # Merges per-pair JSONs into consolidated report
  results/                           # Output directory
  go/                                # Go as host language
    call_python3/                    # MetaFFI correctness + benchmarks
    call_java/                       # MetaFFI correctness + benchmarks
    without_metaffi/                 # Native + gRPC baselines (benchmarks only)
  python3/                           # Python3 as host language
    call_go/
    call_java/
    without_metaffi/
  java/                              # Java as host language
    call_go/
    call_python3/
    without_metaffi/
```

Guest modules (the code being called) live in `sdk/test_modules/guest_modules/{go,java,python3}/`.

See [plan.md](plan.md) for the full methodology, JSON schema, statistical approach, and implementation phases.
