#!/usr/bin/env bash
set -e

# build java code containing foreign functions
echo kotlinc TestFuncs.kt
kotlinc TestFuncs.kt -d .

echo metaffi -c --idl Test.proto -g
metaffi -c --idl Test.proto -g

