#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
import sys
from pyjarowinkler import distance
from unidecode import unidecode
import re
from functools import lru_cache
import math

# usage: ./monotranslate.py src.freqlist tgt.freqlist < src_input > tgt_output

SMOOTH = 5

vowels = r"[aeiouy]"

with open(sys.argv[1],"rb") as packed:
    srclist = msgpack.load(packed, encoding="utf-8", use_list=False)

with open(sys.argv[2],"rb") as packed:
    tgtlist = msgpack.load(packed, encoding="utf-8", use_list=False)

@lru_cache(maxsize=1024)
def deacc_dewov(word):
    deacc = unidecode(word)
    devow = ""
    for char in word:
        if not re.search(vowels, char):
            devow += char
    dd = re.sub(vowels, "", unidecode(word))
    return (deacc, devow, dd, dd[:2], len(dd))

@lru_cache(maxsize=1024)
def srcwordfreq(word, wordlist):
    return wordfreq(word, srclist)

@lru_cache(maxsize=1024)
def tgtwordfreq(word, wordlist):
    return wordfreq(word, tgtlist)

def wordfreq(word, wordlist):
    (_, _, _, prefix, length) = deacc_dewov(word)
    key = (prefix, length)
    if key in wordlist and word in wordlist[key]:
        count = wordlist[key][word]
    else:
        count = 0
    return (count + SMOOTH) / wordlist[None][None]

@lru_cache(maxsize=65536)
def translate(srcword):
    (_, _, _, prefix, src_length) = deacc_dewov(srcword)
    # init with keeping the original word
    tgt_best = srcword
    tgt_best_score = simscore(srcword, srcword)
    print("SRC: " + srcword + " TGT: " + tgt_best + " " + str(tgt_best_score), file=sys.stderr)
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
                    tgt_best = tgtword
                    tgt_best_score = score
                    print("SRC: " + srcword + " TGT: " + tgt_best + " " + str(tgt_best_score), file=sys.stderr)
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

@lru_cache(maxsize=1024)
def simscore(srcword, tgtword):
    src_freq = wordfreq(srcword, srclist)
    tgt_freq = wordfreq(tgtword, tgtlist)
    freq_ratio = math.log(src_freq)/math.log(tgt_freq)
    freq_sim = min(freq_ratio, 1/freq_ratio)
    jw_sim = jw_safe(srcword, tgtword)
    jw_sim_deacc = jw_safe(deacc_dewov(srcword)[0], deacc_dewov(tgtword)[0])
    jw_sim_devow = jw_safe(deacc_dewov(srcword)[1], deacc_dewov(tgtword)[1])
    sim = freq_sim * jw_sim * jw_sim_deacc * jw_sim_devow
    return sim

for line in sys.stdin:
    translated = []
    for word in line.split():
        (translation, score) = translate(word.lower())
        if(word.istitle()):
            translation = translation.title()
        if(word.isupper()):
            translation = translation.upper()
        translated.append(translation)
    print(" ".join(translated))

