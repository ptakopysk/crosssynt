#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
import sys
from pyjarowinkler import distance
from unidecode import unidecode
import re

# usage: ./monotranslate.py src.freqlist tgt.freqlist < src_input > tgt_output

SMOOTH = 5

vowels = r"[aeiouy]"

with open(sys.argv[1],"rb") as packed:
    srclist = msgpack.load(packed, encoding="utf-8", use_list=False)
src_total = srclist['']

with open(sys.argv[2],"rb") as packed:
    tgtlist = msgpack.load(packed, encoding="utf-8", use_list=False)
tgt_total = tgtlist['']

def deacc_dewov(word):
    return re.sub(vowels, "", unidecode(word))

def translate(srcword, srclist, tgtlist):
    src_count = SMOOTH
    if srcword in srclist:
        src_count += srclist[srcword]
    src_freq = src_count / src_total
    src_deacc_dewov = deacc_dewov(srcword)
    src_prefix = src_deacc_dewov[:2]
    src_length = len(src_deacc_dewov)
    tgt_best = "UNKNWON"
    tgt_best_score = 0
    # print("SRC: " + srcword + " count: " + str(src_count) + " freq: " + str(src_freq), file=sys.stderr)
    for tgt_length in [src_length, src_length-1, src_length+1]:
        for tgtword, tgt_count in tgtlist[(src_prefix,tgt_length)].items():
            # print("TGT: " + tgtword + " count: " + str(tgt_count), file=sys.stderr)
            tgt_freq = (tgt_count + SMOOTH) / tgt_total
            tgt_deacc_dewov = deacc_dewov(tgtword)
            score = simscore(srcword, tgtword, src_freq, tgt_freq, src_deacc_dewov, tgt_deacc_dewov)
            if score > tgt_best_score:
                print("SRC: " + srcword + " TGT: " + tgtword + " " + str(score), file=sys.stderr)
                tgt_best_score = score
                tgt_best = tgtword
    return (tgt_best, tgt_best_score)

def simscore(srcword, tgtword, src_freq, tgt_freq, src_deacc_dewov, tgt_deacc_dewov):
    freq_sim = min(src_freq/tgt_freq, tgt_freq/src_freq)
    jw_sim = distance.get_jaro_distance(srcword, tgtword)
    if (src_deacc_dewov == tgt_deacc_dewov):
        # esp. in case it equals "" as jw does not like that;
        # because the prefixes must match, eiether none or both are empty
        jw_sim_dd = 1
    else:
        jw_sim_dd = distance.get_jaro_distance(src_deacc_dewov, tgt_deacc_dewov)
    sim = freq_sim * jw_sim * jw_sim_dd
    return sim

for line in sys.stdin:
    line = line.rstrip().lower() # TODO project case
    (translation, score) = translate(line, srclist, tgtlist)
    print(translation, score)

