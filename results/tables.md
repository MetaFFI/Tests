# MetaFFI Cross-Language Performance Comparison

## Benchmark Results Summary

- **Result files**: 15 of 18 expected
- **Missing result files**: 3
- **Benchmarks passed**: 147
- **Benchmarks failed**: 3

### Missing Result Files

- **go->python3 [cpython]**: `go_to_python3_cpython.json`
- **go->java [metaffi]**: `go_to_java_metaffi.json`
- **go->java [jni]**: `go_to_java_jni.json`

### Failed Benchmarks

- **go->python3 [metaffi]** object_method: xcall_no_params_ret bug: Index 0 out of bounds (CDTS size: 0)
- **java->python3 [metaffi]** object_method: xcall_no_params_ret bug: Index 0 out of bounds (CDTS size: 0)
- **python3->java [metaffi]** callback: Failed to load entity in module C:\src\github.com\MetaFFI\sdk\test_modules\guest_modules\java\test_b


## Go -> Java

| Scenario | metaffi (mean) | jni (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | MISSING | MISSING | MISSING |
| array_echo_100 | MISSING | MISSING | MISSING |
| array_echo_1000 | MISSING | MISSING | MISSING |
| array_echo_10000 | MISSING | MISSING | MISSING |
| array_sum_10 | MISSING | MISSING | 456.7 us |
| array_sum_100 | MISSING | MISSING | 385.5 us |
| array_sum_1000 | MISSING | MISSING | 622.4 us |
| array_sum_10000 | MISSING | MISSING | 698.9 us |
| callback | MISSING | MISSING | 807.6 us |
| error_propagation | MISSING | MISSING | 424.7 us |
| object_method | MISSING | MISSING | 491.0 us |
| primitive_echo | MISSING | MISSING | 653.7 us |
| string_echo | MISSING | MISSING | 663.6 us |
| void_call | MISSING | MISSING | 845.9 us |

## Go -> Python3

| Scenario | metaffi (mean) | cpython (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | MISSING | MISSING | MISSING |
| array_echo_100 | MISSING | MISSING | MISSING |
| array_echo_1000 | MISSING | MISSING | MISSING |
| array_echo_10000 | MISSING | MISSING | MISSING |
| array_sum_10 | 0 ns | MISSING | 241.2 us |
| array_sum_100 | 0 ns | MISSING | 292.6 us |
| array_sum_1000 | 551.8 us | MISSING | 320.8 us |
| array_sum_10000 | 5.99 ms | MISSING | 854.6 us |
| callback | 0 ns | MISSING | 617.7 us |
| error_propagation | 0 ns | MISSING | 319.9 us |
| object_method | FAIL | MISSING | 355.7 us |
| primitive_echo | 0 ns | MISSING | 223.4 us |
| string_echo | 0 ns | MISSING | 273.5 us |
| void_call | 0 ns | MISSING | 276.6 us |

## Java -> Go

| Scenario | metaffi (mean) | jni (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | 183.3 us | 2.7 us | 1.91 ms |
| array_echo_100 | 1.30 ms | 2.7 us | 2.52 ms |
| array_echo_1000 | 12.13 ms | 3.3 us | 1.98 ms |
| array_echo_10000 | 126.73 ms | 8.8 us | 2.02 ms |
| array_sum_10 | MISSING | MISSING | MISSING |
| array_sum_100 | MISSING | MISSING | MISSING |
| array_sum_1000 | MISSING | MISSING | MISSING |
| array_sum_10000 | MISSING | MISSING | MISSING |
| callback | 24.4 us | 1.9 us | 3.04 ms |
| error_propagation | 12.3 us | 2.8 us | 2.86 ms |
| object_method | 19.8 us | 5.4 us | 8.76 ms |
| primitive_echo | 19.2 us | 1.1 us | 2.97 ms |
| string_echo | 49.8 us | 3.3 us | 2.02 ms |
| void_call | 9.5 us | 1.1 us | 3.31 ms |

## Java -> Python3

| Scenario | metaffi (mean) | jep (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | 116.8 us | MISSING | MISSING |
| array_echo_100 | 1.02 ms | MISSING | MISSING |
| array_echo_1000 | 11.06 ms | MISSING | MISSING |
| array_echo_10000 | 307.52 ms | MISSING | MISSING |
| array_sum_10 | MISSING | 16.6 us | 2.17 ms |
| array_sum_100 | MISSING | 16.5 us | 1.90 ms |
| array_sum_1000 | MISSING | 19.2 us | 1.83 ms |
| array_sum_10000 | MISSING | 43.8 us | 3.00 ms |
| callback | 51.7 us | 23.3 us | 3.02 ms |
| error_propagation | 39.9 us | 83.9 us | 1.50 ms |
| object_method | FAIL | 24.1 us | 1.77 ms |
| primitive_echo | 11.8 us | 16.5 us | 2.60 ms |
| string_echo | 29.6 us | 18.4 us | 2.48 ms |
| void_call | 7.1 us | 8.8 us | 3.35 ms |

## Python3 -> Go

| Scenario | metaffi (mean) | ctypes (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | 43.7 us | 4.4 us | 170.4 us |
| array_echo_100 | 267.0 us | 3.9 us | 180.2 us |
| array_echo_1000 | 2.40 ms | 4.4 us | 183.8 us |
| array_echo_10000 | 20.42 ms | 5.1 us | 202.3 us |
| array_sum_10 | MISSING | MISSING | MISSING |
| array_sum_100 | MISSING | MISSING | MISSING |
| array_sum_1000 | MISSING | MISSING | MISSING |
| array_sum_10000 | MISSING | MISSING | MISSING |
| callback | 13.2 us | 2.6 us | 1.26 ms |
| error_propagation | 4.8 us | 4.1 us | 190.8 us |
| object_method | 14.9 us | 7.2 us | 169.2 us |
| primitive_echo | 14.5 us | 2.6 us | 172.4 us |
| string_echo | 14.8 us | 4.7 us | 179.9 us |
| void_call | 10.3 us | 2.1 us | 171.0 us |

## Python3 -> Java

| Scenario | metaffi (mean) | jpype (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | MISSING | MISSING | MISSING |
| array_echo_100 | MISSING | MISSING | MISSING |
| array_echo_1000 | MISSING | MISSING | MISSING |
| array_echo_10000 | MISSING | MISSING | MISSING |
| array_sum_10 | 20.5 us | 1.4 us | 1.64 ms |
| array_sum_100 | 85.1 us | 2.1 us | 1.06 ms |
| array_sum_1000 | 767.2 us | 9.9 us | 1.15 ms |
| array_sum_10000 | 6.31 ms | 86.5 us | 2.75 ms |
| callback | FAIL | 10.9 us | 2.36 ms |
| error_propagation | 15.1 us | 31.3 us | 657.5 us |
| object_method | 20.6 us | 9.0 us | 1.20 ms |
| primitive_echo | 11.7 us | 1.2 us | 1.32 ms |
| string_echo | 12.3 us | 5.3 us | 1.28 ms |
| void_call | 9.6 us | 920 ns | 1.40 ms |


# Code Complexity Comparison

## Summary by Mechanism

| Mechanism | Count | Avg SLOC | Avg Benchmark SLOC | Avg Languages | Avg Files | Avg Max CC |
|---|---|---|---|---|---|---|
| grpc | 6 | 462 | 462 | 3.0 | 2.0 | 11.0 |
| metaffi | 6 | 928 | 335 | 1.0 | 2.3 | 10.5 |
| native | 6 | 397 | 397 | 1.7 | 2.8 | 6.7 |

## Per-Pair Comparison (Benchmark-Only SLOC)

Excludes MetaFFI correctness tests for fair cross-mechanism comparison.

| Pair | MetaFFI | Native | gRPC |
|---|---|---|---|
| go->java | 339 | 456 (jni) | 591 |
| go->python3 | 352 | 448 (cpython) | 511 |
| java->go | 386 | 517 (jni) | 449 |
| java->python3 | 410 | 311 (jep) | 440 |
| python3->go | 246 | 444 (ctypes) | 371 |
| python3->java | 277 | 205 (jpype) | 412 |

## Languages Required per Pair

| Pair | MetaFFI | Native | gRPC |
|---|---|---|---|
| go->java | 1 (Go) | 1 (Go) | 3 (Go, Java, Protobuf) |
| go->python3 | 1 (Go) | 1 (Go) | 3 (Go, Protobuf, Python) |
| java->go | 1 (Java) | 3 (C, Go, Java) | 3 (Go, Java, Protobuf) |
| java->python3 | 1 (Java) | 1 (Java) | 3 (Java, Protobuf, Python) |
| python3->go | 1 (Python) | 3 (C, Go, Python) | 3 (Go, Protobuf, Python) |
| python3->java | 1 (Python) | 1 (Python) | 3 (Java, Protobuf, Python) |
