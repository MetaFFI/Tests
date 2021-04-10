#!/usr/bin/env bash

# build java code containing foreign functions
echo kotlinc TestFuncs.kt
kotlinc TestFuncs.kt -d ..

echo openffi -c --idl Test.proto -t
openffi -c --idl Test.proto -t

rm *.class
cd ..
rm -r META-INF