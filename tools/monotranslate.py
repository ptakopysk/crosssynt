#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
import sys
from pyjarowinkler import distance
from unidecode import unidecode
import re
from functools import lru_cache

# usage: ./monotranslate.py src.freqlist tgt.freqlist < src_input > tgt_output

SMOOTH = 5

vowels = r"[aeiouy]"

with open(sys.argv[1],"rb") as packed:
    srclist = msgpack.load(packed, encoding="utf-8", use_list=False)

with open(sys.argv[2],"rb") as packed:
    tgtlist = msgpack.load(packed, encoding="utf-8", use_list=False)

@lru_cache(maxsize=1024)
def deacc_dewov(word):
    dd = re.sub(vowels, "", unidecode(word))
    return (dd, dd[:2], len(dd))

@lru_cache(maxsize=1024)
def srcwordfreq(word, wordlist):
    return wordfreq(word, srclist)

@lru_cache(maxsize=1024)
def tgtwordfreq(word, wordlist):
    return wordfreq(word, tgtlist)

def wordfreq(word, wordlist):
    (dd, prefix, length) = deacc_dewov(word)
    key = (prefix, length)
    if key in wordlist and word in wordlist[key]:
        count = wordlist[key][word]
    else:
        count = 0
    return (count + SMOOTH) / wordlist[None][None]

def translate(srcword):
    (src_dd, prefix, src_length) = deacc_dewov(srcword)
    tgt_best = "UNKNWON"
    tgt_best_score = 0
    # print("SRC: " + srcword + " count: " + str(src_count) + " freq: " + str(src_freq), file=sys.stderr)
    #if (src_prefix,src_length) in tgtlist and srcword in tgtlist[(src_prefix,tgt_length):
    #    tgt_best = srcword
    #    tgt_best_score = simscore(srcword, srcword, src_freq, tgtlist[(src_prefix,tgt_length):
    for tgt_length in [src_length, src_length-1, src_length+1]:
        if (prefix,tgt_length) in tgtlist:
             for tgtword in tgtlist[(prefix,tgt_length)]:
                # print("TGT: " + tgtword + " count: " + str(tgt_count), file=sys.stderr)
                score = simscore(srcword, tgtword)
                if score > tgt_best_score:
                    print("SRC: " + srcword + " TGT: " + tgtword + " " + str(score), file=sys.stderr)
                    tgt_best_score = score
                    tgt_best = tgtword
    return (tgt_best, tgt_best_score)

# Jaro Winkler that can take emtpy words
@lru_cache(maxsize=1024)
def jw_safe(srcword, tgtword):
    if srcword == '' or tgtword == '':
        # 1 if both empty
        # 0.5 if one is length 1
        # 0.33 if one is length 2
        # ...
        return 1/(len(srcword)+len(tgtword)+1)
    else:
        return distance.get_jaro_distance(srcword, tgtword)

def simscore(srcword, tgtword):
    src_freq = wordfreq(srcword, srclist)
    tgt_freq = wordfreq(tgtword, tgtlist)
    freq_sim = min(src_freq/tgt_freq, tgt_freq/src_freq)
    jw_sim = jw_safe(srcword, tgtword)
    jw_sim_dd = jw_safe(deacc_dewov(srcword)[0], deacc_dewov(tgtword)[0])
    sim = freq_sim * jw_sim * jw_sim_dd
    return sim

for line in sys.stdin:
    line = line.rstrip().lower() # TODO project case
    (translation, score) = translate(line)
    print(translation, score)

