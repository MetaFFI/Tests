#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../../Guests/Python3/libraries/python-string-utils/build_guest.sh .
cp ../../../../../Guests/Python3/libraries/python-string-utils/python_string_utils.proto .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo Running Tests
go get -u
go build
./main
echo Tests ran successfully!

echo Starting cleanup...

echo Deleting guest files
rm build_guest.sh
rm python_string_utils.proto
rm *.py
rm -r __pycache__

echo Delete host file
rm python_string_utils_MetaFFIHost.go
rm main

echo Done Go to Python3