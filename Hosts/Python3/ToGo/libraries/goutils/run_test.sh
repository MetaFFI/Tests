#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../../Guests/Go/libraries/goutils/build_guest.sh .
cp ../../../../../Guests/Go/libraries/goutils/go.mod .
cp ../../../../../Guests/Go/libraries/goutils/Test.proto .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
python3 -m unittest Main_test.TestSanity

echo Deleting guest files
rm build_guest.sh
rm go.mod
rm Test.proto
rm Test_OpenFFIGuest.so
rm -R __pycache__

echo Delete host file
rm Test_OpenFFIHost.py

echo Done Python3 to Go