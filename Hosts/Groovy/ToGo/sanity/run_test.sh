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

echo Compiling Test Code
groovyc -cp "./..:Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_test.groovy

echo running tests
#cd ..
#cp sanity/Test_OpenFFIGuest.so .
groovy -cp ".:Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_test
#rm Test_OpenFFIGuest.so

echo Deleting guest files
rm build_guest.sh
rm go.mod
rm Test.proto
rm TestFuncs.go
rm Test_OpenFFIGuest.so

echo Delete host file
rm Test_OpenFFIHost.jar
rm -r sanity

echo Done Java to Go