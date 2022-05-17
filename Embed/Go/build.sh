#!/usr/bin/env bash

echo metaffi -c --idl Main_test.go -n TestFuncs.py -g -h go --host-options "package=sanity"
metaffi -c --idl Main_test.go -n TestFuncs.py -g -h go --host-options "package=sanity"