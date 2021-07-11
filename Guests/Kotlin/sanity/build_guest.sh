#!/usr/bin/env bash
set -e

# build java code containing foreign functions
echo kotlinc TestFuncs.kt
kotlinc TestFuncs.kt -d .

echo openffi -c --idl Test.proto -g
openffi -c --idl Test.proto -g

