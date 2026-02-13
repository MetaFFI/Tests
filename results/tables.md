# MetaFFI Cross-Language Performance Comparison

## Benchmark Results Summary

- **Result files**: 18 of 18 expected
- **Missing result files**: 0
- **Benchmarks passed**: 180
- **Benchmarks failed**: 0


## Go -> Java

| Scenario | metaffi (mean) | jni (mean) | grpc (mean) |
|---|---|---|---|
| array_sum_10 | 50.2 µs | 458.1 ns | 0.000 ns |
| array_sum_100 | 94.3 µs | 647.0 ns | 0.000 ns |
| array_sum_1000 | 610.4 µs | 1.9 µs | 0.000 ns |
| array_sum_10000 | 5.93 ms | 11.5 µs | 225.3 µs |
| callback | 34.7 µs | 137.9 ns | 243.2 µs |
| error_propagation | 41.4 µs | 562.9 ns | 0.000 ns |
| object_method | 65.7 µs | 831.6 ns | 0.000 ns |
| primitive_echo | 39.3 µs | 144.7 ns | 159.1 µs |
| string_echo | 46.5 µs | 982.9 ns | 152.7 µs |
| void_call | 34.0 µs | 87.0 ns | 271.3 µs |

## Go -> Python3

| Scenario | metaffi (mean) | cpython (mean) | grpc (mean) |
|---|---|---|---|
| array_sum_10 | 12.5 µs | 466.1 ns | 334.3 µs |
| array_sum_100 | 62.0 µs | 1.0 µs | 337.1 µs |
| array_sum_1000 | 576.0 µs | 11.4 µs | 405.1 µs |
| array_sum_10000 | 6.06 ms | 117.6 µs | 818.0 µs |
| callback | 23.6 µs | 294.1 ns | 586.5 µs |
| error_propagation | 16.4 µs | 189.1 ns | 224.8 µs |
| object_method | 9.8 µs | 322.8 ns | 422.3 µs |
| primitive_echo | 3.6 µs | 118.2 ns | 433.8 µs |
| string_echo | 6.7 µs | 201.6 ns | 383.8 µs |
| void_call | 2.6 µs | 88.4 ns | 387.9 µs |

## Java -> Go

| Scenario | metaffi (mean) | jni (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | 12.1 µs | 2.7 µs | 1.17 ms |
| array_echo_100 | 15.5 µs | 2.9 µs | 970.9 µs |
| array_echo_1000 | 58.4 µs | 2.9 µs | 1.14 ms |
| array_echo_10000 | 455.8 µs | 4.7 µs | 857.5 µs |
| callback | 12.4 µs | 1.5 µs | 1.01 ms |
| error_propagation | 5.6 µs | 2.9 µs | 618.6 µs |
| object_method | 9.7 µs | 5.1 µs | 902.1 µs |
| primitive_echo | 8.0 µs | 1.2 µs | 1.12 ms |
| string_echo | 18.7 µs | 2.8 µs | 1.37 ms |
| void_call | 4.2 µs | 1.1 µs | 1.19 ms |

## Java -> Python3

| Scenario | metaffi (mean) | jep (mean) | grpc (mean) |
|---|---|---|---|
| array_sum_10 | 16.5 µs | 10.7 µs | 343.6 µs |
| array_sum_100 | 21.7 µs | 13.0 µs | 349.2 µs |
| array_sum_1000 | 70.2 µs | 16.4 µs | 379.0 µs |
| array_sum_10000 | 562.3 µs | 43.2 µs | 896.7 µs |
| callback | 23.9 µs | 11.7 µs | 649.7 µs |
| error_propagation | 19.3 µs | 63.7 µs | 334.3 µs |
| object_method | 10.1 µs | 21.6 µs | 336.3 µs |
| primitive_echo | 6.6 µs | 12.6 µs | 367.5 µs |
| string_echo | 14.7 µs | 12.9 µs | 378.3 µs |
| void_call | 3.3 µs | 5.9 µs | 498.7 µs |

## Python3 -> Go

| Scenario | metaffi (mean) | ctypes (mean) | grpc (mean) |
|---|---|---|---|
| array_echo_10 | 27.4 µs | 4.7 µs | 187.3 µs |
| array_echo_100 | 178.1 µs | 4.8 µs | 187.5 µs |
| array_echo_1000 | 1.70 ms | 4.6 µs | 202.4 µs |
| array_echo_10000 | 17.24 ms | 4.9 µs | 230.9 µs |
| callback | 11.6 µs | 2.4 µs | 1.48 ms |
| error_propagation | 4.3 µs | 3.8 µs | 213.6 µs |
| object_method | 13.5 µs | 7.4 µs | 195.5 µs |
| primitive_echo | 9.2 µs | 2.5 µs | 201.0 µs |
| string_echo | 9.4 µs | 4.6 µs | 203.0 µs |
| void_call | 6.2 µs | 1.8 µs | 179.9 µs |

## Python3 -> Java

| Scenario | metaffi (mean) | jpype (mean) | grpc (mean) |
|---|---|---|---|
| array_sum_10 | 65.5 µs | 1.5 µs | 1.18 ms |
| array_sum_100 | 109.1 µs | 2.2 µs | 1.07 ms |
| array_sum_1000 | 685.5 µs | 9.7 µs | 1.46 ms |
| array_sum_10000 | 7.71 ms | 90.1 µs | 2.28 ms |
| callback | 69.4 µs | 16.9 µs | 2.25 ms |
| error_propagation | 51.1 µs | 40.9 µs | 773.3 µs |
| object_method | 160.8 µs | 6.2 µs | 1.44 ms |
| primitive_echo | 46.6 µs | 1.2 µs | 1.39 ms |
| string_echo | 47.4 µs | 5.6 µs | 1.28 ms |
| void_call | 40.9 µs | 675.0 ns | 1.55 ms |


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
