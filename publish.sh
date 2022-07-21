#!/bin/bash

set -xe

VERSION=$1

SOURCEDIST=csvmodel-${VERSION}.tar.gz
BINDIST=csvmodel-${VERSION}-py3-none-any.whl

cram README.md

python -m build

twine check dist/$SOURCEDIST dist/$BINDIST

twine upload dist/$SOURCEDIST dist/$BINDIST
