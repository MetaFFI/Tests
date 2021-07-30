#!/usr/bin/env bash

set -e

echo Copying go test code
cp ../../../../Guests/Go/sanity/build_guest.sh .
cp ../../../../Guests/Go/sanity/go.mod .
cp ../../../../Guests/Go/sanity/Test.proto .
cp ../../../../Guests/Go/sanity/TestFuncs.go .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
groovy -cp ".:Test_MetaFFIHost.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:$METAFFI_HOME/protobuf-java-3.15.2.jar" Main_test
echo Tests ran successfully!

echo Starting cleanup...

echo Deleting guest files
rm build_guest.sh
rm go.mod
rm Test.proto
rm TestFuncs.go
rm Test_MetaFFIGuest.so

echo Delete host file
rm Test_MetaFFIHost.jar

echo Done Groovy to Go