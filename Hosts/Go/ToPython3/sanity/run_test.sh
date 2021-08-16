#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../Guests/Python3/sanity/build_guest.sh .
cp ../../../../Guests/Python3/sanity/Test.json .
cp ../../../../Guests/Python3/sanity/TestFuncs.py .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo Running Tests
go get -u
go test
echo Tests ran successfully!

echo Starting cleanup...

echo Deleting guest files
rm build_guest.sh
rm Test.json
rm TestFuncs.py
rm Test_MetaFFIGuest.py
rm -r __pycache__

echo Delete host file
rm Test_MetaFFIHost.go
rm go.sum

echo Done Go to Python3
