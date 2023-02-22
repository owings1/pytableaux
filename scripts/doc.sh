#!/bin/bash
set -e
dir_="$(dirname "$0")"
cd "$dir_/../doc"
make clean doctest html