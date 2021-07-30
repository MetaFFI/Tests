#!/usr/bin/env bash

# build java code containing foreign functions
echo scalac TestFuncs.scala
scalac TestFuncs.scala -d .

echo metaffi -c --idl Test.proto -g
metaffi -c --idl Test.proto -g
