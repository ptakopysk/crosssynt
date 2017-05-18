#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
from collections import defaultdict, Counter
import sys
from unidecode import unidecode
import re
from functools import lru_cache

vowels = r"[aeiouy]"

@lru_cache(maxsize=65536)
def devow(deacc):
    return re.sub(vowels, "", deacc)

@lru_cache(maxsize=65536)
def line2key(line):
    line = devow(unidecode(line))
    return (line[:2], len(line))

freqlist=defaultdict(lambda : Counter())

with open(sys.argv[1], "r") as infile:
    total = 0
    for line in infile:
        line = line.rstrip().lower()
        key = line2key(line)
        freqlist[key][line] += 1
        total += 1
    freqlist[None][None] = total

with open(sys.argv[2], "wb") as outfile:
    msgpack.dump(freqlist, outfile)


