#!/bin/bash

mkdir -p para
cp sample/OpenSubtitles* para/

mkdir -p treebanks
cp sample/*conllu treebanks/

./new.sh cs_small pl_small
cd run
./all-cs_small-pl_small.sh

