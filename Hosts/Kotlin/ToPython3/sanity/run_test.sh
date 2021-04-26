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

echo Compiling Test Code
kotlinc -cp "Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_test.kt

echo running tests
kotlin -cp ".:./sanity:Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_testKt
echo Tests ran successfully!

echo Starting cleanup...

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm TestFuncs.py
rm Test_OpenFFIGuest.py

echo Delete host file
rm Test_OpenFFIHost.jar
rm Main_testKt.class
rm -r META-INF

echo Done Java to Python3