#!/usr/bin/env bash

echo openffi -c --idl python_string_utils.proto -f go
openffi -c --idl python_string_utils.proto -f go