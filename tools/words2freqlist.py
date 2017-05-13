#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
from collections import defaultdict
import sys

freqlist=defaultdict(int)

with open(sys.argv[1], "r") as infile:
    for line in infile:
        line = line.rstrip()
        freqlist[line] += 1
        freqlist[''] += 1

with open(sys.argv[2], "wb") as outfile:
    msgpack.dump(freqlist, outfile)


