#!/bin/bash

mkdir -p treebanks
cd treebanks

wget "https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-1827/ud-treebanks-v1.4.tgz?sequence=4&isAllowed=y" -O ud-treebanks-v1.4.tgz
tar -zxvf ud-treebanks-v1.4.tgz
rm ud-treebanks-v1.4.tgz

for f in ud-treebanks-v1.4/*/*.conllu
do
    ln -s $f
done

# no forms
rm ja_ktc*
rm en_esl*

