#!/usr/bin/env bash

# build java code containing foreign functions
echo groovyc TestFuncs.groovy -d .
groovyc TestFuncs.groovy -d .

echo openffi -c --idl Test.proto -g
openffi -c --idl Test.proto -g
