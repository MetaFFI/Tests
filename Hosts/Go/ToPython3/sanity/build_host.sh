#!/usr/bin/env bash

echo openffi -c --idl Test.proto -f go --host-options "package=sanity"
openffi -c --idl Test.proto -f go --host-options "package=sanity"