#!/bin/sh
set -e

coverage run --source src --omit '*/__init__.py' -m pytest test
coverage report -m
coverage html