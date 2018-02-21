#!/bin/bash

l=$1
mkdir -p wiki
wget https://dumps.wikimedia.org/${l}wiki/latest/${l}wiki-latest-pages-articles-multistream.xml.bz2 -O wiki/$l.xml.bz2
cd wiki
bunzip2 $l.xml.bz2
cd ..
wikiextractor/WikiExtractor.py --txt wiki/$l.xml -o - | sed 's/<[^>]*>//g' | gzip > wiki/$l.txt.gz
rm wiki/$l.xml

