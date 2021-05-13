#!/usr/bin/env bash

set -e

echo Copying Java test code
cp ../../../../Guests/Java/sanity/build_guest.sh .
cp ../../../../Guests/Java/sanity/Test.proto .
cp ../../../../Guests/Java/sanity/TestFuncs.java .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
go get -t
go test

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm TestFuncs.java
rm Test_OpenFFIGuest.jar
rm -r sanity

echo Delete host file
rm Test_OpenFFIHost.go

echo Done Go to Java