#!/usr/bin/env bash

echo openffi -c --idl python_string_utils.proto -f go --host-options "package=PythonStringUtils"
openffi -c --idl python_string_utils.proto -f go --host-options "package=PythonStringUtils"