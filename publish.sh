#!/bin/bash

set -xe

cram README.md

python -m build

twine check dist/*

twine upload dist/*
