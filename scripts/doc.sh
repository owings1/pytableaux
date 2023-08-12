#!/bin/bash
set -e
dir_="$(dirname "$0")"
cd "$dir_/../doc"
if [ "$#" -eq 0 ]; then
    targets="doctest html"
else
    targets="$@"
fi
make clean $targets