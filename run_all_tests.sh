#!/usr/bin/env bash
set -e

RED='\033[0;31m'
NORMAL='\033[0m' # No Color

cd Hosts
rootpath=$PWD
runs=$(find . | grep 'run_test.sh')
for run in $runs
do
  dir=$(dirname $run)
  runscript=$(basename $run)

	echo -e "${RED}==== Running $run ====${NORMAL}"
	cd "$dir"
	./"$runscript"

  cd "$rootpath"
done

echo "${RED}==== All Tests Executed Successfully ====${NORMAL}"