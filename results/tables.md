# MetaFFI Cross-Language Performance Comparison

## Benchmark Results Summary

- **Result files**: 18 of 18 expected
- **Missing result files**: 0
- **Benchmarks passed**: 198
- **Benchmarks failed**: 0


## Go -> Java

| Scenario | metaffi (mean) | jni (mean) | grpc (mean) |
|---|---|---|---|
| any_echo_100 | 103.9 µs | 11.6 µs | 200.7 µs |
| array_sum_10 | 5.2 µs | 427.9 ns | 153.6 µs |
| array_sum_100 | 5.5 µs | 555.9 ns | 151.5 µs |
| array_sum_1000 | 7.3 µs | 1.8 µs | 154.8 µs |
| array_sum_10000 | 34.1 µs | 14.3 µs | 248.5 µs |
| callback | 15.7 µs | 158.4 ns | 277.1 µs |
| error_propagation | 15.9 µs | 736.1 ns | 137.9 µs |
| object_method | 12.5 µs | 888.1 ns | 155.9 µs |
| primitive_echo | 6.5 µs | 175.9 ns | 167.9 µs |
| string_echo | 9.6 µs | 826.3 ns | 158.3 µs |
| void_call | 1.3 µs | 103.4 ns | 305.2 µs |

## Go -> Python3

| Scenario | metaffi (mean) | cpython (mean) | grpc (mean) |
|---|---|---|---|
| any_echo_100 | 223.2 µs | 1.6 µs | 463.7 µs |
| array_sum_10 | 5.4 µs | 634.8 ns | 345.0 µs |
| array_sum_100 | 6.7 µs | 1.4 µs | 404.4 µs |
| array_sum_1000 | 27.0 µs | 15.1 µs | 438.1 µs |
| array_sum_10000 | 247.7 µs | 168.0 µs | 834.2 µs |
| callback | 26.8 µs | 375.0 ns | 590.0 µs |
| error_propagation | 2.6 µs | 272.6 ns | 301.7 µs |
| object_method | 10.7 µs | 461.6 ns | 397.0 µs |
| primitive_echo | 3.6 µs | 157.0 ns | 357.3 µs |
| string_echo | 8.0 µs | 267.9 ns | 346.7 µs |
| void_call | 484.6 ns | 91.9 ns | 297.4 µs |

## Java -> Go

| Scenario | metaffi (mean) | jni (mean) | grpc (mean) |
|---|---|---|---|
| any_echo_100 | 237.5 µs | 21.4 µs | 190.1 µs |
| array_echo_10 | 6.6 µs | 3.8 µs | 140.2 µs |
| array_echo_100 | 6.4 µs | 3.4 µs | 141.1 µs |
| array_echo_1000 | 7.4 µs | 4.0 µs | 144.9 µs |
| array_echo_10000 | 12.7 µs | 6.8 µs | 163.7 µs |
| callback | 16.2 µs | 2.1 µs | 288.5 µs |
| error_propagation | 8.1 µs | 3.4 µs | 157.4 µs |
| object_method | 12.1 µs | 6.7 µs | 141.7 µs |
| primitive_echo | 9.1 µs | 1.8 µs | 174.1 µs |
| string_echo | 24.1 µs | 4.4 µs | 162.6 µs |
| void_call | 1.7 µs | 1.7 µs | 337.7 µs |

## Java -> Python3

| Scenario | metaffi (mean) | jep (mean) | grpc (mean) |
|---|---|---|---|
| any_echo_100 | 327.9 µs | 63.7 µs | 403.4 µs |
| array_sum_10 | 7.8 µs | 16.9 µs | 334.9 µs |
| array_sum_100 | 9.6 µs | 18.2 µs | 350.6 µs |
| array_sum_1000 | 27.6 µs | 22.1 µs | 418.3 µs |
| array_sum_10000 | 213.1 µs | 55.3 µs | 927.7 µs |
| callback | 30.1 µs | 17.6 µs | 667.8 µs |
| error_propagation | 7.7 µs | 74.3 µs | 354.8 µs |
| object_method | 12.9 µs | 28.2 µs | 335.3 µs |
| primitive_echo | 8.2 µs | 17.6 µs | 378.2 µs |
| string_echo | 21.7 µs | 18.6 µs | 353.1 µs |
| void_call | 325.0 ns | 8.9 µs | 513.2 µs |

## Python3 -> Go

| Scenario | metaffi (mean) | ctypes (mean) | grpc (mean) |
|---|---|---|---|
| any_echo_100 | 190.6 µs | 19.9 µs | 263.3 µs |
| array_echo_10 | 5.8 µs | 5.3 µs | 224.3 µs |
| array_echo_100 | 6.0 µs | 4.7 µs | 215.2 µs |
| array_echo_1000 | 7.4 µs | 5.1 µs | 239.1 µs |
| array_echo_10000 | 18.4 µs | 5.5 µs | 250.1 µs |
| callback | 9.9 µs | 2.8 µs | 1.60 ms |
| error_propagation | 3.8 µs | 4.6 µs | 239.5 µs |
| object_method | 12.3 µs | 8.7 µs | 219.8 µs |
| primitive_echo | 6.7 µs | 3.0 µs | 220.1 µs |
| string_echo | 8.1 µs | 5.4 µs | 232.0 µs |
| void_call | 2.6 µs | 1.9 µs | 215.4 µs |

## Python3 -> Java

| Scenario | metaffi (mean) | jpype (mean) | grpc (mean) |
|---|---|---|---|
| any_echo_100 | 79.2 µs | 1.9 µs | 242.8 µs |
| array_sum_10 | 7.8 µs | 1.4 µs | 213.8 µs |
| array_sum_100 | 8.8 µs | 1.4 µs | 228.7 µs |
| array_sum_1000 | 19.5 µs | 1.9 µs | 215.1 µs |
| array_sum_10000 | 132.7 µs | 5.1 µs | 362.0 µs |
| callback | 19.3 µs | 6.2 µs | 1.41 ms |
| error_propagation | 16.8 µs | 29.7 µs | 261.4 µs |
| object_method | 20.1 µs | 4.1 µs | 210.6 µs |
| primitive_echo | 11.2 µs | 1.3 µs | 298.1 µs |
| string_echo | 11.1 µs | 4.6 µs | 211.5 µs |
| void_call | 2.9 µs | 600.0 ns | 362.8 µs |


# Code Complexity Comparison

## Summary by Mechanism

| Mechanism | Count | Avg SLOC | Avg Benchmark SLOC | Avg Languages | Avg Files | Avg Max CC |
|---|---|---|---|---|---|---|
| grpc | 6 | 584 | 584 | 3.0 | 2.0 | 20.8 |
| metaffi | 6 | 1089 | 445 | 1.0 | 2.3 | 11.3 |
| native | 6 | 1532 | 1532 | 2.0 | 6.7 | 18.2 |

## Per-Pair Comparison (Benchmark-Only SLOC)

Excludes MetaFFI correctness tests for fair cross-mechanism comparison.

| Pair | MetaFFI | Native | gRPC |
|---|---|---|---|
| go->java | 481 | 641 (jni) | 742 |
| go->python3 | 470 | 588 (cpython) | 644 |
| java->go | 537 | 6745 (jni) | 586 |
| java->python3 | 527 | 402 (jep) | 558 |
| python3->go | 306 | 552 (ctypes) | 468 |
| python3->java | 351 | 264 (jpype) | 507 |

## Languages Required per Pair

| Pair | MetaFFI | Native | gRPC |
|---|---|---|---|
| go->java | 1 (Go) | 2 (C, Go) | 3 (Go, Java, Protobuf) |
| go->python3 | 1 (Go) | 2 (C, Go) | 3 (Go, Protobuf, Python) |
| java->go | 1 (Java) | 3 (C, Go, Java) | 3 (Go, Java, Protobuf) |
| java->python3 | 1 (Java) | 1 (Java) | 3 (Java, Protobuf, Python) |
| python3->go | 1 (Python) | 3 (C, Go, Python) | 3 (Go, Protobuf, Python) |
| python3->java | 1 (Python) | 1 (Python) | 3 (Java, Protobuf, Python) |
