#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../Guests/Go/sanity/build_guest.sh .
cp ../../../../Guests/Go/sanity/go.mod .
cp ../../../../Guests/Go/sanity/Test.proto .
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
rm Test.proto
rm TestFuncs.go
rm Test_OpenFFIGuest.so

echo Delete host file
rm Test_OpenFFIHost_pb2.py

echo Done Python3 to Go