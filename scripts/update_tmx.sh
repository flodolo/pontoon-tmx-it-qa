#! /usr/bin/env bash

script_path=$(dirname "$0")
root_path=$script_path/..

cd $root_path/data

echo "Downloading updated TMX from Pontoon"

url="https://pontoon.mozilla.org/translation-memory/it.all-projects.tmx"
output="it.all-projects.tmx"

max_attempts=5
delay=10

for ((attempt=1; attempt<=max_attempts; attempt++)); do
    echo "Attempt $attempt of $max_attempts..."

    curl \
      --fail \
      --compressed \
      --retry 5 \
      --retry-delay "$delay" \
      --retry-connrefused \
      -o "$output" \
      "$url"

    # Check if download succeeded and file is non-empty
    if [ -s "$output" ]; then
        echo "✅ Download succeeded and file is not empty."
        break
    else
        echo "⚠️ File is empty or download failed. Retrying in $delay seconds..."
        sleep "$delay"
    fi
done

# Final check
if [ ! -s "$output" ]; then
    echo "❌ Failed to download a valid TMX file after $max_attempts attempts."
    exit 1
fi
