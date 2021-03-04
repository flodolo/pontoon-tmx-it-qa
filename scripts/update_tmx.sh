#! /usr/bin/env bash

script_path=$(dirname "$0")
root_path=$script_path/..

cd $root_path/data

echo "Downloading updated TMX from Pontoon"
curl -o it.all-projects.tmx --compressed https://pontoon.mozilla.org/translation-memory/it.all-projects.tmx
