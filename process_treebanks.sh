#!/bin/bash

mkdir -p treebanks_processed
for l in `cat langs`;
do
    for t in train dev test
    do
        cat treebanks/$l-ud-$t.conllu treebanks/${l}_*-ud-$t.conllu | \
        tools/simplify_deprel.py | \
        grep -v '^#' | grep -v '^[0-9]*-' \
            > treebanks_processed/$l-ud-$t.conllu
    done
done

mv treebanks treebanks_orig
mv treebanks_processed treebanks

