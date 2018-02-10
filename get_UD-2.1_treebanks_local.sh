#!/bin/bash

ln -s /net/data/universal-dependencies-2.1

mkdir -p treebanks
cd treebanks

for f in ../universal-dependencies-2.1/*/*.conllu
do
    ln -s $f
done

