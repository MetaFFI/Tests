#!/usr/bin/env bash

# build java code containing foreign functions
echo scalac TestFuncs.scala
scalac TestFuncs.scala -d .

echo openffi -c --idl Test.proto -g
openffi -c --idl Test.proto -g
