#! /usr/bin/env bash

script_path=$(dirname "$0")
root_path=$script_path/..

cd $root_path/data

echo "Downloading updated TMX from Pontoon"

url="https://pontoon.mozilla.org/translation-memory/it.all-projects.tmx"
output="it.all-projects.tmx"

max_attempts=5
delay=10
min_size=$((1024 * 1024)) # 1 MB

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

    # GitHub seems to download a 4 Kb file when failing, so need to check for
    # a minimum size.
    filesize=$(wc -c <"$output")
    if [ "$filesize" -ge "$min_size" ]; then
        size_human=$(du -h "$output" | cut -f1)
        echo "✅ Download succeeded, file size OK ($size_human)."
        break
    else
        echo "⚠️ File too small ($filesize bytes). Retrying in $delay seconds..."
        sleep "$delay"
    fi
done

# Final check
if [ ! -s "$output" ]; then
    echo "❌ Failed to download a valid TMX file after $max_attempts attempts."
    exit 1
fi
