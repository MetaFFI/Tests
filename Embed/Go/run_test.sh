#!/usr/bin/env bash

set -e


echo compile metaffi
./build.sh

echo Running Tests
go get -u
go test
echo Tests ran successfully!

echo Starting cleanup...

echo Deleting guest files
rm TestFuncs.py
rm TestFuncs_MetaFFIGuest.py
rm -r __pycache__

echo Delete host file
rm TestFuncs_MetaFFIHost.go
rm go.sum

echo Done Go to Python3
