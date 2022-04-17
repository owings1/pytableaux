#!/bin/sh
set -e

coverage run --source pytableaux --omit '*/__init__.py' -m pytest test
coverage report -m
coverage html