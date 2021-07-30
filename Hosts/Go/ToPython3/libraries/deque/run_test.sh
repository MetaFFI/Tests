#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../../Guests/Python3/libraries/deque/build_guest.sh .
cp ../../../../../Guests/Python3/libraries/deque/deque.proto .

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
rm deque.proto
rm *.py
rm -r __pycache__

echo Delete host file
rm deque_MetaFFIHost.go
rm main

echo Done Go to Python3