#!/usr/bin/env bash

set -e

echo Copying go test code
cp ../../../../../Guests/Go/libraries/goutils/build_guest.sh .
cp ../../../../../Guests/Go/libraries/goutils/Test.proto .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
go test

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm Test_MetaFFIGuest.so

echo Delete host file
rm Test_MetaFFIHost.go

echo Done Go to Go