#! /usr/bin/env bash

script_path=$(dirname "$0")
root_path=$script_path/..

cd $root_path/data

echo "Downloading updated TMX from Pontoon"
# Retry up to 5 times, wait 10 seconds between retries
curl \
  --fail \
  --compressed \
  --retry 5 \
  --retry-delay 10 \
  --retry-connrefused \
  -o it.all-projects.tmx \
  https://pontoon.mozilla.org/translation-memory/it.all-projects.tmx
