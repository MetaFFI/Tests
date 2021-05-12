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
scalac -cp ".:Test_OpenFFIHost.jar:Test_OpenFFIGuest.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_test.scala

echo running tests
java -cp ".:Test_OpenFFIHost.jar:Test_OpenFFIGuest.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar:/usr/share/scala/lib/scala-library.jar:/snap/groovy/current/lib/groovy-3.0.4.jar" Main_test

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm Test_OpenFFIGuest.jar
rm TestFuncs.groovy
rm *.class
rm -r sanity

echo Delete host file
rm Test_OpenFFIHost.jar

echo Done Scala to Groovy