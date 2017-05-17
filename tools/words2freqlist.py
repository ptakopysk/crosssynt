#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
from collections import defaultdict, Counter
import sys
from unidecode import unidecode
import re

vowels = r"[aeiouy]"

freqlist=defaultdict(lambda : Counter())

with open(sys.argv[1], "r") as infile:
      for line in infile:
        line = line.rstrip().lower()
        line_deacc = unidecode(line)
        line_deacc_devow = re.sub(vowels, "", line_deacc)
        prefix = line_deacc_devow[:2]
        length = len(line_deacc_devow)        
        freqlist[(prefix,length)][line] += 1
        freqlist[None][None] += 1

with open(sys.argv[2], "wb") as outfile:
    msgpack.dump(freqlist, outfile)


