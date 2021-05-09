#!/usr/bin/env bash

set -e

echo Copying Scala test code
cp ../../../../Guests/Scala/sanity/build_guest.sh .
cp ../../../../Guests/Scala/sanity/Test.proto .
cp ../../../../Guests/Scala/sanity/TestFuncs.scala .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo Compiling Test Code
javac -cp "./..:Test_OpenFFIHost.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar" Main_test.java

echo running tests
cd ..
cp sanity/Test_OpenFFIGuest.jar .
java -cp ".:sanity/Test_OpenFFIHost.jar:Test_OpenFFIGuest.jar:$OPENFFI_HOME/xllr.openjdk.bridge.jar:$OPENFFI_HOME/protobuf-java-3.15.2.jar:/usr/share/scala/lib/scala-library.jar" sanity.Main_test
rm Test_OpenFFIGuest.jar
cd sanity

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm Test_OpenFFIGuest.jar
rm TestFuncs.scala
rm *.class

echo Delete host file
rm Test_OpenFFIHost.jar

echo Done Java to Go