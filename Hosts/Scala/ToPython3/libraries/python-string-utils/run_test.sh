#!/usr/bin/env bash

set -e

echo Copying python3 test code
cp ../../../../../Guests/Python3/libraries/python-string-utils/build_guest.sh .
cp ../../../../../Guests/Python3/libraries/python-string-utils/python_string_utils.proto .

echo building guest
./build_guest.sh

echo building host
./build_host.sh

echo Running Tests
scalac -cp ".:python_string_utils_MetaFFIHost.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:$METAFFI_HOME/protobuf-java-3.15.2.jar" Main_test.scala
scala -cp ".:python_string_utils_MetaFFIHost.jar:$METAFFI_HOME/xllr.openjdk.bridge.jar:$METAFFI_HOME/protobuf-java-3.15.2.jar" Main_test
echo Tests ran successfully!

echo Starting cleanup...

echo Deleting guest files
rm build_guest.sh
rm python_string_utils.proto
rm *.py

echo Delete host file
rm python_string_utils_MetaFFIHost.jar
rm *.class

echo Done Go to Python3