#! /usr/bin/env bash

script_path="$( cd -- "$( dirname -- "${BASH_SOURCE[0]:-$0}"; )" &> /dev/null && pwd 2> /dev/null; )";

cd $script_path

./update_tmx.sh
./check_strings.sh
