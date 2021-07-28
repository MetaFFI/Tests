#!/usr/bin/env bash

set -e

echo Copying go test code
cp ../../../../Guests/Go/sanity/build_guest.sh .
cp ../../../../Guests/Go/sanity/go.mod .
cp ../../../../Guests/Go/sanity/Test.proto .
cp ../../../../Guests/Go/sanity/TestFuncs.go .

echo building guest
./build_guest.sh

rm go.mod
rm TestFuncs.go

echo building host
./build_host.sh

echo running tests
go mod init test
go test -tags=maintest

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm Test_OpenFFIGuest.so

echo Delete host file
rm Test_OpenFFIHost.go

echo Done Go to Go