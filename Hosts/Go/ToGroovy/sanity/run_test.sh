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
go get -t
go test

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm TestFuncs.groovy
rm Test_OpenFFIGuest.jar
rm TestFuncs.class

echo Delete host file
rm Test_OpenFFIHost.go


echo Done Go to Groovy