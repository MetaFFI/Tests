# MetaFFI Test Status

Updated: 2026-02-13

## Current State

- Runner was migrated to a **strict config-driven protocol** (`tests/run_all_tests.py --config ...`).
- Full thesis run is **not yet re-executed** after these changes.
- Current `tests/results/*.json` are mixed because smoke/subset runs were executed for validation.
- Consolidation currently succeeds (`18/18` files load), but current values are not thesis-final until a full thesis config rerun is completed.

## Implemented In This Pass

1. Config-driven orchestration (fail-fast):
- `tests/run_all_tests.py` now requires `--config`.
- Missing keys / unknown keys / invalid values fail immediately.
- Added preset configs:
  - `tests/configs/thesis_config.yml`
  - `tests/configs/fast_test_config.yml`
  - `tests/configs/only_correctness_config.yml`

2. Uncertainty pass integration:
- Runner executes repeated benchmark runs (`repeats` from config).
- Per-repeat files written to `tests/results/repeats/<run_id>/run_XX/`.
- Canonical result files in `tests/results/*.json` are aggregated using:
  - **global pooled mean across all iterations from all repeats**.
- Per-benchmark repeat metadata is written under `repeat_analysis`.

3. Liveness/progress:
- Runner prints stage/repeat/triple progress.
- Long-running commands emit periodic `[alive]` heartbeat lines with elapsed time.

4. 0 ns mitigation (Go benchmark harnesses):
- Added adaptive micro-batching controls via env:
  - `METAFFI_TEST_BATCH_MIN_ELAPSED_NS`
  - `METAFFI_TEST_BATCH_MAX_CALLS`
- Applied to all Go benchmark suites:
  - `tests/go/call_python3/benchmark_test.go`
  - `tests/go/call_java/benchmark_test.go`
  - `tests/go/without_metaffi/call_python3_cpython/benchmark_test.go`
  - `tests/go/without_metaffi/call_java_jni/benchmark_test.go`
  - `tests/go/without_metaffi/call_python3_grpc/benchmark_test.go`
  - `tests/go/without_metaffi/call_java_grpc/benchmark_test.go`

5. Report/table updates:
- `tests/generate_tables.py`
  - UTF-8 write + latency formatting uses `µs`.
  - Sub-ns/ns values shown with decimals (no forced integer rounding).
- `tests/generate_report.py`
  - Benchmark protocol section now includes repeats + batching params.
  - Added **Repeat-Mean Tables** (`run_i_mean`, `mean_of_repeat_means`, `global_pooled_mean`).
  - Figure 7 now excludes `Avg Benchmark SLOC` and `Avg Files` from heatmap (kept in table).

5.1 Consolidation robustness fix:
- `tests/consolidate_results.py` now loads only canonical expected triple files
  (`<host>_to_<guest>_<mechanism>.json` from the 18 expected triples),
  and ignores temp/debug files like `_tmp_*`.

6. Java->Go MetaFFI array-path optimization (large-array hotspot):
- Root cause identified in JVM runtime manager path:
  - per-element construct/traverse for Java arrays incurred very high JNI overhead.
  - even after earlier `Get*ArrayRegion(..., len=1)` improvement, 1D bulk paths were still missing.
- Implemented 1D bulk fast paths in `sdk/runtime_manager/jvm/cdts_java_wrapper.cpp`:
  - Added templated helpers for **all primitive numeric types + bool**.
  - Added **handle[]** fast path.
  - Added fast path on both directions:
    - traverse CDTS -> Java array (`on_traverse_array` now short-circuits recursion for supported 1D arrays)
    - construct Java array -> CDTS (`on_construct_array_metadata` + `on_construct_cdt_array` manual construction)
  - Enforced fail-fast checks (type/length mismatches throw immediately).
- Rebuilt and redeployed:
  - `cmake --build cmake-build-debug --target api_jvm -j 8`
  - `cmake --build cmake-build-debug --target xllr.jvm -j 8`
- Measured in `tests/java/call_go`:
  - `warmup=20`, `iterations=200`:
    - `array_echo[10000]`: **~53,650,397 ns -> ~418,420 ns** (~128x faster)
  - `warmup=100`, `iterations=10000`:
    - `array_echo[10000]`: **~455,760 ns**
    - full `TestBenchmark#testAllBenchmarks` wall-time: **~8.1s** (was previously ~766.6s in thesis run output).
- Side effect observed in correctness:
  - `tests/java/call_go` now has 2 `xfail` checks that **unexpectedly pass**:
    - `testMake3DArray`
    - `testMakeRaggedArray`
  - These are currently test-expectation failures (not runtime errors), and should be reclassified if this behavior is accepted.

7. Python3 CDTS serializer 1D primitive fast path:
- Added direct 1D primitive sequence fill path in:
  - `sdk/cdts_serializer/cpython3/cdts_python3_serializer.cpp`
- Supported fast-filled element types:
  - `float32`, `float64`
  - `int8`, `int16`, `int32`, `int64`
  - `uint8`, `uint16`, `uint32`, `uint64`
  - `bool`
- Behavior:
  - Only activates for homogeneous 1D primitive arrays.
  - Keeps fail-fast conversion/range checks.
  - Falls back to existing generic recursive path for non-supported/mixed cases.

## Validations Run

- Python syntax checks:
  - `python -m py_compile tests/run_all_tests.py tests/generate_tables.py tests/generate_report.py tests/consolidate_results.py`

- Go compile checks (no tests run):
  - `go test -run TestDoesNotExist -count=1 ./...` in each modified Go benchmark package

- Runner smoke run:
  - `python tests/run_all_tests.py --config tests/configs/fast_test_config.yml`
  - Passed for selected subset, repeat aggregation succeeded.

- Focused zero-floor sanity check:
  - `python tests/run_all_tests.py --config <temp go->java jni config>`
  - Produced non-zero means in `go_to_java_jni.json` with adaptive batching metadata.

- Java->Go focused benchmark validation:
  - `mvn.cmd test "-Dtest=TestBenchmark#testAllBenchmarks" -pl .` in `tests/java/call_go`
  - validated at:
    - `METAFFI_TEST_WARMUP=20`, `METAFFI_TEST_ITERATIONS=200`
    - `METAFFI_TEST_WARMUP=100`, `METAFFI_TEST_ITERATIONS=10000`

- Java->Go correctness spot checks after optimization:
  - `mvn.cmd test "-Dtest=TestCorrectness#testGetThreeBuffers" -pl .` passed.
  - full `TestCorrectness` reports 2 failures due `xfail unexpectedly passed` (see above), no runtime exception in those two cases.

- Python3 serializer validation:
  - built runtime plugin: `cmake --build cmake-build-debug --target xllr.python3 -j 8`
  - `python -m pytest -q tests/python3/call_go/test_correctness.py -k "array" --tb=short` -> `3 passed, 6 xfailed`
  - `mvn.cmd test "-Dtest=TestBenchmark#testAllBenchmarks" -pl .` in `tests/java/call_python3` with `warmup=20`, `iterations=200` passed.

## Open Items (Next Required Steps)

1. Execute full thesis protocol (required before publication):
- `python tests/run_all_tests.py --config tests/configs/thesis_config.yml`

2. Regenerate thesis artifacts from full run (if not already triggered by config):
- `python tests/consolidate_results.py`

3. Review post-run `tests/results/report.md` and confirm:
- Uniform protocol (`warmup=100`, `measured=10000`, `repeats=5`).
- 0 ns mitigation is acceptable in final tables/figures.
- Callback/object_method status remains as expected after full rerun.

4. Update this file again with the thesis-final snapshot after full rerun.

5. Decide how to handle new `xfail unexpectedly passed` outcomes in `tests/java/call_go`:
- Option A: update tests to regular PASS assertions.
- Option B: keep current `xfail` expectations and treat as known deviation during this phase.

6. Continue optimization pass for remaining high-cost scenarios if needed:
- next candidate remains Python/JVM serializer-side profiling for Java->Python / Python->Java large-array cases.
