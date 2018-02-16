#!/usr/bin/env python3
#coding: utf-8

from math import log
import sys
import gzip
from collections import deque, defaultdict

# compute D_KL(P||Q)
# i.e. we approximate P by Q
# projection from lang1 to lang2

# usage: python3 klcpos3.py source.conllu target.conllu

N = 3
END = 'BOUNDARY'
SMOOTH = 0.5

def new_ngram_deque():
    return deque(N * [END])

# read counts from files
def readfile(filename):
    result = defaultdict(int)
    if filename.endswith(".gz"):
        inputfile = gzip.open(filename, 'rt', encoding='utf-8')
    else:
        inputfile = open(filename, 'r')
    ngram = new_ngram_deque()
    
    for line in inputfile:
        line = line.strip()
        if line:
            ngram.popleft()
            order, word, tag = line.split('\t')[:3]
            ngram.append(tag)
            result[tuple(ngram)] += 1
        else:
            # end of sentence
            for i in range(N-1):
                ngram.popleft()
                ngram.append(END)
                result[tuple(ngram)] += 1

    inputfile.close()
    return result

# the source language which we use to train the parser (Q)
source_counts = readfile(sys.argv[1])
source_sum = sum(source_counts.values())

# the language we want to parse (P)
target_counts = readfile(sys.argv[2])
target_sum = sum(target_counts.values())

# smoothing
for ngram in target_counts:
    if not ngram in source_counts:
        source_counts[ngram] = SMOOTH
        source_sum += SMOOTH

dkl = 0

for ngram in target_counts:
    target_prob = target_counts[ngram]/target_sum 
    source_prob = source_counts[ngram]/source_sum 
    dkl += target_prob * log(target_prob/source_prob)

print(dkl)

