#!/bin/bash

set -e

cd $REPO_HOME/doc

make clean
make html

cd $REPO_HOME

python src/web.py