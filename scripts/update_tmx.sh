#! /usr/bin/env bash

script_path=$(dirname "$0")
root_path=$script_path/..

cd $root_path/data

echo "Downloading updated TMX from Pontoon"
curl -o it.all-projects.tmx --compressed https://pontoon.mozilla.org/translation-memory/it.all-projects.tmx

# Temporary fix for 1681653
echo "Fixing chr(3) error"
sed -i '' $'s/\x03//g' it.all-projects.tmx
