#!/bin/bash

set -xe

cp setup.cfg setup.cfg_backup

function cleanup () {
  mv setup.cfg_backup setup.cfg
}

trap cleanup ERR

# bump version
sed -r 's/version = ([0-9]+)/echo "version = $((\1+1))"/e' setup.cfg > setup.cfg_new
mv setup.cfg_new setup.cfg

VERSION=$(awk '/version = [0-9]+/ { print $3 }' setup.cfg)

SOURCEDIST=csvmodel-${VERSION}.tar.gz
BINDIST=csvmodel-${VERSION}-py3-none-any.whl

cram README.md

python -m build

twine check dist/$SOURCEDIST dist/$BINDIST

twine upload --verbose dist/$SOURCEDIST dist/$BINDIST

echo "*******************************************************"
echo "* Now commit setup.cfg and tag the commit as v${VERSION}"
echo "*******************************************************"

rm setup.cfg_backup
