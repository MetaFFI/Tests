#!/usr/bin/env bash

set -e

python3 run_test.py ./Hosts/Go/ToPython3/sanity
python3 run_test.py ./Hosts/Go/ToPython3/libraries/collections
python3 run_test.py ./Hosts/Go/ToPython3/libraries/builtins
python3 run_test.py ./Hosts/Go/ToPython3/libraries/python-string-utils
python3 run_test.py ./Hosts/Go/ToPython3/libraries/pandas
python3 run_test.py ./Hosts/Go/ToJava/sanity
python3 run_test.py ./Hosts/Python3/ToGo/sanity
python3 run_test.py ./Hosts/Python3/ToGo/libraries/go-mcache
python3 run_test.py ./Hosts/Python3/ToJava/sanity
python3 run_test.py ./Hosts/Java/ToPython3/sanity
python3 run_test.py ./Hosts/Java/ToGo/sanity
python3 run_test.py ./Hosts/Java/ToPython3/libraries/python_string_utils
python3 run_test.py ./Hosts/Java/ToPython3/libraries/collections
python3 run_test.py ./Hosts/Java/ToPython3/libraries/builtins

