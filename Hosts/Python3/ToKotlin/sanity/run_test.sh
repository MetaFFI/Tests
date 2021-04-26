#!/usr/bin/env bash

set -e

echo Copying Kotlin test code
cp ../../../../Guests/Kotlin/sanity/build_guest.sh .
cp ../../../../Guests/Kotlin/sanity/Test.proto .
cp ../../../../Guests/Kotlin/sanity/TestFuncs.kt .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo running tests
python3 -m unittest Main_test.TestSanity

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm TestFuncs.kt
rm Test_OpenFFIGuest.jar

echo Delete host file
rm Test_OpenFFIHost_pb2.py
rm TestFuncs.class

echo Done Go to Kotlin