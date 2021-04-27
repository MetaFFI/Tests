#!/usr/bin/env bash

set -e

echo Copying Groovy test code
cp ../../../../Guests/Groovy/sanity/build_guest.sh .
cp ../../../../Guests/Groovy/sanity/Test.proto .
cp ../../../../Guests/Groovy/sanity/TestFuncs.groovy .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo Compiling Test Code
javac -cp "./..:Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_test.java

echo running tests
cd ..
java -cp ".:sanity/Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" sanity.Main_test
cd sanity

echo Deleting guest files
rm build_guest.sh
rm go.mod
rm Test.proto
rm TestFuncs.go
rm Test_OpenFFIGuest.so

echo Delete host file
rm Test_OpenFFIHost.jar
rm Main_test.class

echo Done Java to Go