#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../Guests/Python3/sanity/build_guest.sh .
cp ../../../../Guests/Python3/sanity/Test.proto .
cp ../../../../Guests/Python3/sanity/TestFuncs.py .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
go test

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm TestFuncs.py
rm Test_OpenFFIGuest.py

echo Delete host file
rm Test_OpenFFIHost.go

echo Done Go to Python3