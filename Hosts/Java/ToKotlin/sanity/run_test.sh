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

echo Compiling Test Code
javac -cp "./..:Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_test.java

echo running tests
cd ..
cp sanity/Test_OpenFFIGuest.jar .
java -cp ".:sanity/Test_OpenFFIHost.jar:Test_OpenFFIGuest.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar:/snap/kotlin/current/lib/kotlin-stdlib.jar" sanity.Main_test
rm Test_OpenFFIGuest.jar
rm -r META-INF
cd sanity

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm Test_OpenFFIGuest.jar
rm TestFuncs.kt
rm *.class

echo Delete host file
rm Test_OpenFFIHost.jar

echo Done Java to Go