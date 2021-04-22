#!/usr/bin/env bash

# build java code containing foreign functions
echo javac TestFuncs.java
javac TestFuncs.java

echo openffi -c --idl Test.proto -t
openffi -c --idl Test.proto -t
