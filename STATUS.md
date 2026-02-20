# MetaFFI Test Status

Updated: 2026-02-15
Canonical dataset timestamp: 2026-02-15 (`tests/results/consolidated.json`)

This file is the handoff source of truth for a new agent/session. `tests/plan.md` was updated to match this status.

## Canonical Snapshot (Current)

- Result files: `18/18`
- Missing result files: `0`
- Benchmarks: `198 passed, 0 failed`
- Comparison cells present: `66/66`

Latest void_call results (true void(void), refreshed 2026-02-15):

| Pair | MetaFFI | Native | gRPC |
|---|---|---|---|
| go->java | 2.4 us | 101.8 ns (jni) | 216.9 us |
| go->python3 | 1.7 us | 95.7 ns (cpython) | 257.1 us |
| java->go | 1.3 us | 1.4 us (jni) | 280.6 us |
| java->python3 | 1.4 us | 7.2 us (jep) | 386.3 us |
| python3->go | 2.6 us | 1.6 us (ctypes) | 177.8 us |
| python3->java | 4.1 us | 500.0 ns (jpype) | 307.3 us |

Pair-level mean vs gRPC:

- MetaFFI mean is lower than gRPC in `6/6` language pairs.
- Remaining MetaFFI > gRPC is concentrated in `4/66` scenarios (see Open Issues).

## How To Run (Runner + Configs)

Primary runner:

- `python tests/run_all_tests.py --config <config.yml>`
- `python tests/run_all_tests.py --clear-config <config.yml>`
- `python tests/run_all_tests.py --config <config.yml> --scenario <scenario>[,<scenario>...]`

Important runner behavior:

- Strict config mode (unknown/missing keys are fail-fast errors).
- Resume state is config-scoped: `tests/results/repeats/_state/<config_stem>.json`.
- Repeats are saved under: `tests/results/repeats/<timestamp>__<config_stem>/run_XX/...`.
- `--scenario` reruns only selected benchmark scenarios and merges only those scenario rows into canonical result files.

Configs currently in use:

- `tests/configs/thesis_config.yml`: publication pipeline, benchmarks-only, `N=5`, warmup `100`, measured `10000`.
- `tests/configs/fast_test_config.yml`: fast smoke pipeline.
- `tests/configs/only_correctness_config.yml`: correctness-only.
- `tests/configs/thesis_array_sum_only_config.yml`: targeted array_sum optimization pass.
- `tests/configs/thesis_array_echo_only_config.yml`: targeted array_echo optimization pass.
- `tests/configs/thesis_any_echo_only_config.yml`: targeted any_echo optimization pass.
- `tests/configs/tmp_java_go_only_config.yml`: targeted Java->Go debug/optimization run.
- `_tmp_*` configs are ad-hoc debug configs and not canonical publication configs.

## Report/Tables Pipeline

Canonical post-run pipeline:

1. `python tests/consolidate_results.py`
2. `consolidate_results.py` fail-fast calls:
 - `tests/generate_tables.py`
 - `tests/generate_report.py`

Generated artifacts:

- `tests/results/consolidated.json` (canonical machine-readable dataset)
- `tests/results/tables.md` (comparison tables)
- `tests/results/report.md` (thesis-oriented narrative + figures)
- `tests/results/report_figures/*.png`

Note:

- `tests/generate_report.py` now includes an explicit **Optimizations Implemented** section in `report.md`.

## Latest Completed Work

### java->go [metaffi] crash fix — Go object handle lifecycle (2026-02-15)

- **Root cause**: Double-free of Go object handles via CDT destructor. When a Go
  object handle (with its `release` function pointer) was returned to Java, the CDT
  `free()` method would invoke Go's `Releaser()` on CDT destruction even though Java
  had already taken ownership. Subsequent uses of the now-released handle caused
  `EXCEPTION_ACCESS_VIOLATION` / JVM `ShouldNotReachHere()` abort.
- **Fix (3 files)**:
  - `sdk/runtime_manager/jvm/cdts_java_wrapper.cpp`:
    - `on_construct_handle`: null `release` pointer when converting Java `MetaFFIHandle`
      to input CDT (Java retains ownership, CDT must not release).
    - `fast_construct_array`: same fix for array elements.
  - `sdk/api/jvm/accessor/metaffi_api_accessor.cpp`:
    - New `null_foreign_handle_releasers()`: recursive CDT tree walker that nulls
      `release` pointers for non-JVM handles (`runtime_id != JVM_RUNTIME_ID`),
      preserving JNI global-ref cleanup for JVM handles.
    - New `null_foreign_handle_releasers_buffer()`: buffer-level helper for cdts[N].
    - Output path (`cdts_to_java`): calls `null_foreign_handle_releasers` after each
      CDT element is converted to a Java object.
    - Input path (`java_to_cdts`): calls `null_foreign_handle_releasers` after
      building input CDTs from Java parameters.
    - Safety net (`free_cdts`): calls `null_foreign_handle_releasers_buffer` on the
      entire cdts buffer before `xllr_free_cdts_buffer`, catching any missed paths.
- **Verified**: All 11 scenarios (including `any_echo[100]` and `object_method`)
  pass at 10,000 iterations with zero warnings and zero crashes.

### void_call fix to true void(void) (2026-02-15)

- Added `NoOp()`/`noOp()`/`no_op()` true void(void) functions to all 3 guest modules (Go, Java, Python3).
- Updated all 18 benchmark implementations (6 MetaFFI, 6 native, 6 gRPC) to call the new void(void) functions.
- Native bridges updated: CPython calls `PyObject_CallObject(func, NULL)` (no args tuple), JNI calls `()V` signature, ctypes/JNI bridges got new `GoNoOp`/`noOp` exports.
- gRPC servers call `NoOp()`/`noOp()`/`no_op()` instead of `WaitABit(req.Ms)`, clients send empty `VoidCallRequest`.
- Report scenario renamed from `void_call_no_payload` to `void_call_void_void`.
- Rebuilt: Go guest DLL, Java guest JAR, ctypes bridge DLL, JNI bridge DLL, Java gRPC server JAR, Go gRPC server exe.
- Full rerun: 90/90 passed (18 triples x 5 repeats), 0 failures.
- `consolidated.json`, `tables.md`, `report.md` all regenerated.

### Java-host int64->void fast path (prior session)

- `sdk/api/jvm/metaffi/api/accessor/Caller.java`: fast path for `(int64)->void`, bypassing generic `java_to_cdts`.
- `sdk/api/jvm/accessor/metaffi_api_accessor.cpp`: JNI `set_cdt_int64` native implementation.

## Open Issues (Priority Order)

### ~~1. `java->go [metaffi]` full benchmark crash~~ — RESOLVED (2026-02-15)

Fixed. See "Latest Completed Work" above for details.

### 2. Remaining MetaFFI > gRPC hotspots — ANALYZED (2026-02-15)

- From canonical dataset:
  - `java->go` `array_echo_10000`: `697,877 ns` vs `412,493 ns` (`1.69x`)
  - `python3->go` `array_echo_10000`: `685,233 ns` vs `257,713 ns` (`2.66x`)
  - `python3->go` `any_echo_100`: `388,637 ns` vs `291,708 ns` (`1.33x`)
  - `python3->java` `array_sum_10000`: `706,682 ns` vs `506,715 ns` (`1.39x`)
- **Root cause**: Inherent CDT format overhead, NOT implementation inefficiency.
  - CDT uses 24 bytes per array element (uint64 type + 8-byte value union + free_required + padding).
  - A 10K-byte array requires ~240KB of CDT memory vs ~10KB raw data (24x overhead).
  - gRPC protobuf uses packed wire format (~1 byte/byte element) with ~24x lower memory footprint.
- **All serializers already optimized**:
  - Go: bulk C functions (`fill_cdts_from_uint8_buffer`, `copy_cdts_to_uint8_buffer`) execute in single CGO call.
  - Java: `set_cdts_from_jni_primitive_array`/`set_jni_primitive_array_region_from_cdts` with bulk JNI + tight C++ loops.
  - Python3: tight C++ loops in `cdts_python3_serializer.cpp`.
- **Conclusion**: This is an architectural trade-off — CDT's per-value type metadata enables schema-less cross-language calls (no `.proto` authoring) at the cost of higher memory overhead for large homogeneous arrays. No further per-element optimization is feasible without redesigning the CDT format (e.g., adding packed primitive array types).

### 3. Python3->Java access violation trace — DIAGNOSED (2026-02-15)

- Repro:
  - `python -m pytest -v tests/python3/call_java/test_correctness.py -k "test_call_callback_add or test_return_callback_add or test_call_transformer or test_return_transformer" --tb=short`
- Current behavior:
  - "Windows fatal exception: access violation" is printed during JVM runtime plugin loading
    (in `xllr_wrapper.py:load_runtime_plugin` → `conftest.py:java_runtime` fixture).
  - All 4 tests pass correctly. Process exits with code 0.
- Root cause:
  - Transient VEH (Vectored Exception Handler) interaction on Windows. Go and JVM both install VEH handlers.
    When the JVM runtime plugin is loaded, a caught access violation triggers Python's `faulthandler` to
    print the stack trace, but the exception is handled and execution continues normally.
- Impact: Cosmetic only. Does not affect correctness, benchmark results, or process stability.
- Resolution: Document as known Windows Go+JVM VEH interaction. Could suppress by disabling Python
  `faulthandler` during JVM loading, but not needed for thesis results.

### 4. `0 ns` timing floor (methodology note)

- Some native paths still report `0 ns` due timer-resolution floor for very fast calls (~100ns).
- Not a correctness failure, but must remain explicitly documented in the thesis.

## Suggested Next Execution Order (For New Agent)

1. ~~Fix Issue #1 (`java->go` crash / handle-release lifecycle).~~ **DONE**
2. ~~Continue hotspot optimization for remaining 10k-array/dynamic cases (Issue #2).~~ **ANALYZED** — inherent CDT format overhead, all serializers already optimized.
3. ~~Re-run full thesis config and regenerate canonical report bundle.~~ **DONE** — consolidation + tables + report regenerated (2026-02-15). 18/18 files, 198/198 benchmarks pass. report.md updated with crash fix + CDT analysis documentation.
4. Final review of `report.md` for thesis submission readiness.

## Files To Read First In New Session

- `tests/STATUS.md` (this file)
- `tests/plan.md` (full project docs, test matrix, schemas)
- `tests/results/report.md` (generated thesis report)
- `tests/results/tables.md` (comparison tables)
- `tests/configs/thesis_config.yml` (publication config)
