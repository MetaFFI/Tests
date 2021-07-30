#!/usr/bin/env bash

echo metaffi -c --idl Test.proto -h go --host-options "package=sanity"
metaffi -c --idl Test.proto -h go --host-options "package=sanity"