#!/usr/bin/env bash

echo openffi -c --idl Test.proto -h go --host-options "package=sanity"
openffi -c --idl Test.proto -h go --host-options "package=sanity"