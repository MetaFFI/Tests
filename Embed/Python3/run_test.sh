#!/usr/bin/env bash

set -e

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
python3 -m unittest Main_test.TestSanity

echo Deleting guest files
rm TestFuncs_MetaFFIGuest.so
rm -R __pycache__

echo Delete host file
rm TestFuncs_MetaFFIHost.py

echo Done Python3 to Go