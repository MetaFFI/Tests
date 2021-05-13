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

echo running tests
python3 -m unittest Main_test.TestSanity

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm TestFuncs.groovy
rm Test_OpenFFIGuest.jar
rm -r sanity

echo Delete host file
rm Test_OpenFFIHost_pb2.py

echo Done Python3 to Groovy