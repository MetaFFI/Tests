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
groovyc -cp ".:Test_MetaFFIHost.jar:Test_MetaFFIGuest.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:$METAFFI_HOME/protobuf-java-3.15.2.jar:/snap/kotlin/current/lib/kotlin-stdlib.jar" Main_test.groovy

echo running tests
java -cp ".:Test_MetaFFIHost.jar:Test_MetaFFIGuest.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:$METAFFI_HOME/protobuf-java-3.15.2.jar:/usr/share/scala/lib/scala-library.jar:/snap/groovy/current/lib/groovy-3.0.4.jar" Main_test

echo Deleting guest files
rm build_guest.sh
rm Test.proto
rm Test_MetaFFIGuest.jar
rm TestFuncs.scala
rm *.class
rm -r sanity

echo Delete host file
rm Test_MetaFFIHost.jar

echo Done Groovy to Scala