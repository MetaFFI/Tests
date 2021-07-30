#!/usr/bin/env bash

# build java code containing foreign functions
echo groovyc TestFuncs.groovy -d .
groovyc TestFuncs.groovy -d .

echo metaffi -c --idl Test.proto -g
metaffi -c --idl Test.proto -g
