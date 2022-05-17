#!/usr/bin/env bash

set -e

echo compile metaffi
./build.sh

echo running tests
python3 -m unittest Main_test.TestSanity

echo Deleting guest files
rm TestFuncs_MetaFFIGuest.so
rm -R __pycache__

echo Delete host file
rm TestFuncs_MetaFFIHost.py

echo Done Python3 to Go