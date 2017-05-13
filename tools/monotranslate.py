#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
from collections import defaultdict
import sys
from pyjarowinkler import distance
import warnings

# usage: ./monotranslate.py src.freqlist tgt.freqlist < src_input > tgt_output

SMOOTH = 5

with open(sys.argv[1],"rb") as packed:
    srclist = msgpack.load(packed, encoding="utf-8", use_list=False)
src_total = srclist['']
del srclist['']

with open(sys.argv[2],"rb") as packed:
    tgtlist = msgpack.load(packed, encoding="utf-8", use_list=False)
tgt_total = tgtlist['']
del tgtlist['']

def translate(srcword, srclist, tgtlist):
    src_count = SMOOTH
    if srcword in srclist:
        src_count += srclist[srcword]
    src_freq = src_count / src_total
    tgt_best = "UNKNWON"
    tgt_best_score = 0
    # warnings.warn("SRC: " + srcword + " count: " + str(src_count) + " freq: " + str(src_freq))
    for tgtword, tgt_count in tgtlist.items():
        # warnings.warn("TGT: " + tgtword + " count: " + str(tgt_count))
        tgt_freq = (tgt_count + SMOOTH) / tgt_total
        score = simscore(srcword, tgtword, src_freq, tgt_freq)
        if score > tgt_best_score:
            print("SRC: " + srcword + " TGT: " + tgtword + " " + str(score), file=sys.stderr)
            tgt_best_score = score
            tgt_best = tgtword
    return (tgt_best, tgt_best_score)

def simscore(srcword, tgtword, src_freq, tgt_freq):
    freq_sim = min(src_freq/tgt_freq, tgt_freq/src_freq)
    jw_sim = distance.get_jaro_distance(srcword, tgtword)
    sim = freq_sim * jw_sim
    return sim

for line in sys.stdin:
    line = line.rstrip()
    (translation, score) = translate(line, srclist, tgtlist)
    print(translation, score)

