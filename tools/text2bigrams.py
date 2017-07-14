#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
from collections import defaultdict, Counter
import sys

START = "[START]"

class Bigrams:

    def __init__(self):
        self.bigrams = defaultdict(lambda : Counter())
    
    def add(self, word, prev):
        self.bigrams[prev][word] += 1
        self.bigrams[None][None] += 1
    
    def readin(self, filename):
        with open(filename, "r") as infile:
            prev = START
            for line in infile:
                word = line.rstrip().lower()
                self.add(word, prev)
                prev = word
    
    def writeout(self, filename):
        with open(filename, "wb") as outfile:
            msgpack.dump(self.bigrams, outfile)

# default: read in text, 1 word per line
if __name__ == "__main__":
    f = Bigrams()
    f.readin(sys.argv[1])
    f.writeout(sys.argv[2])
