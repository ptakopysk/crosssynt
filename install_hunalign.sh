#!/bin/bash

wget ftp://ftp.mokk.bme.hu/Hunglish/src/hunalign/latest/hunalign-1.2.tgz
tar zxvf hunalign-1.2.tgz

cd hunalign-1.2/src/hunalign
make
cd ../../..
ln -s hunalign-1.2/src/hunalign/hunalign

cp -r hunalign-1.2 hunalign-1.2-30g
eds 'quasiglobal_maximalSizeInMegabytes = 4000' 'quasiglobal_maximalSizeInMegabytes = 30000' hunalign-1.2-30g/src/hunalign/alignerTool.cpp 

cd hunalign-1.2-30g/src/hunalign
make
cd ../../..
ln -s hunalign-1.2-30g/src/hunalign/hunalign hunalign-30g
