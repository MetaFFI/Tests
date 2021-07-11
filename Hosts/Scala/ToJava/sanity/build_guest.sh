#!/usr/bin/env bash

# build java code containing foreign functions
echo javac TestFuncs.java
javac TestFuncs.java -d .

echo openffi -c --idl Test.proto -g
openffi -c --idl Test.proto -g
