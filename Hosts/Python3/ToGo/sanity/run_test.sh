#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../Guests/Go/sanity/build_guest.sh .
cp ../../../../Guests/Go/sanity/go.mod .
cp ../../../../Guests/Go/sanity/Test.json .
cp ../../../../Guests/Go/sanity/TestFuncs.go .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
python3 -m unittest Main_test.TestSanity

echo Deleting guest files
rm build_guest.sh
rm go.mod
rm Test.json
rm TestFuncs.go
rm Test_MetaFFIGuest.so
rm -R __pycache__

echo Delete host file
rm Test_MetaFFIHost.py

echo Done Python3 to Go