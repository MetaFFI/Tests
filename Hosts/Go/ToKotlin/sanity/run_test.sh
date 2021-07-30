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
go get -t
go test

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm TestFuncs.kt
rm Test_MetaFFIGuest.jar
rm -r META-INF
rm -r sanity

echo Delete host file
rm Test_MetaFFIHost.go


echo Done Go to Kotlin