The tests are used to test MetaFFI to call from each langauge to all other supported langauges.
It calls each langauge guest test object in `sdk\test_modules\guest_modules`.

For each language call all other supported guest objects in `sdk\test_modules\guest_modules` (except itself).

- The tests must support performance profiling by calculating the time of different segments of the code.
- Additional implementation is requires WITHOUT MetaFFI to use the entities in the guest modules. Similar profiling should be done on both With/Without MetaFFI for effective comparison.
- Both implementation must have the same structure, to allow comparison of lines required to call using MetaFFI vs. Without MetaFFI.
- 