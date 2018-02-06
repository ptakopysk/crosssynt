#!/bin/bash

wget ftp://ftp.mokk.bme.hu/Hunglish/src/hunalign/latest/hunalign-1.2.tgz
tar zxvf hunalign-1.2.tgz

cd hunalign-1.2/src/hunalign
make
cd ../../..
ln -s hunalign-1.2/src/hunalign/hunalign

chmod u+x hunalign-1.2/scripts/partialAlign.py
ln -s hunalign-1.2/scripts/partialAlign.py

touch empty

mkdir -p hunwork

