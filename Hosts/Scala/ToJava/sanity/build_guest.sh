#!/usr/bin/env bash

# build java code containing foreign functions
echo javac TestFuncs.java
javac TestFuncs.java -d .

echo metaffi -c --idl Test.proto -g
metaffi -c --idl Test.proto -g
