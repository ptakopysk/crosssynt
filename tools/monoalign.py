#!/usr/bin/env python3
#coding: utf-8

import msgpack
import io
import sys
from collections import defaultdict, Counter
from pyjarowinkler import distance
from unidecode import unidecode
import re
from functools import lru_cache
import math

# usage: ./monoalign.py src_sentences tgt_sentences trtable,pickle > alignment.slign

# add this to counts
SMOOTH = 0.1

# importance of length match
LENIMP = 0.2

DEBUG = 1

vowels = r"[aeiouy]"

cooccurences = Counter()
sentences_src = ()
sentences_tgt = ()

def init(srcfile, tgtfile):
    global cooccurences, sentences_src, sentences_tgt
    with open(srcfile, "r") as srcfile_f:
        with open(tgtfile, "r") as tgtfile_f:
            srclines = srcfile_f.readlines()
            tgtlines = tgtfile_f.readlines()
            assert len(srclines) == len(tgtlines), "Para data must be same length"
            for sent_index in range(len(srclines)):
                sentences_src.append(srclines[sent_index].split())
                sentences_tgt.append(tgtlines[sent_index].split())
                for src_word in sentences_src[sent_index]:
                    for tgt_word in sentences_tgt[sent_index]
                        cooccurences[(src_word, tgt_word)] += 1
                        
@lru_cache(maxsize=1024)
def isvow(char):
    return re.search(vowels, unidecode(char))

@lru_cache(maxsize=65536)
def deacc_dewov(word):
    deacc = unidecode(word)
    devow = ""
    for char in word:
        if not isvow(char):
            devow += char
    dd = re.sub(vowels, "", deacc)
    return (deacc, devow, dd, dd[:2], len(dd))

# Jaro Winkler that can take emtpy words
@lru_cache(maxsize=65536)
def jw_safe(srcword, tgtword):
    if srcword == '' or tgtword == '':
        # 1 if both empty
        # 0.5 if one is length 1
        # 0.33 if one is length 2
        # ...
        return 1/(len(srcword)+len(tgtword)+1)
    elif srcword == tgtword:
        return 1
    else:
        return distance.get_jaro_distance(srcword, tgtword)

@lru_cache(maxsize=1024)
def lensim(srclen, tgtlen):
    return 1/(1 + LENIMP*abs(srclen-tgtlen))


def dicesim(srcword, tgtword):
    # TODO return dice similarity

# early stopping once similarity falls bellow current best
# (jw is costly)
@lru_cache(maxsize=1024)
def simscore(srcword, tgtword):
    src_dd = deacc_dewov(srcword)
    tgt_dd = deacc_dewov(tgtword)
    if DEBUG >= 2:
        print("deacc: " + src_dd[0] + " " + tgt_dd[0], file=sys.stderr)
        print("devow: " + src_dd[1] + " " + tgt_dd[1], file=sys.stderr)
        print("deacc devow: " + src_dd[2] + " " + tgt_dd[2], file=sys.stderr)
    sim = 1

    len_sim = lensim(len(srcword), len(tgtword))
    if DEBUG >= 2:
        print("lensim  : " + str(len_sim), file=sys.stderr)
    sim *= len_sim
    
    dvlen_sim = lensim(len(src_dd[1]), len(tgt_dd[1]))
    if DEBUG >= 2:
        print("dvlensim: " + str(dvlen_sim), file=sys.stderr)
    sim *= dvlen_sim

    dice_sim = dicesim(srcword, tgtword)
    sim *= dice_sim

    dice_sim_deacc_devow = dicesim(src_dd[2], tgt_dd[2])
    sim *= dice_sim_deacc_devow
    
    jw_sim = jw_safe(srcword, tgtword)
    if DEBUG >= 2:
        print("jwsim  : " + str(jw_sim), file=sys.stderr)
    sim *= jw_sim
    
    jw_sim_deacc = jw_safe(src_dd[0], tgt_dd[0])
    if DEBUG >= 2:
        print("jwsimda: " + str(jw_sim_deacc), file=sys.stderr)
    sim *= jw_sim_deacc
    
    jw_sim_devow = jw_safe(src_dd[1], tgt_dd[1])
    if DEBUG >= 2:
        print("jwsimdv: " + str(jw_sim_devow), file=sys.stderr)
    sim *= jw_sim_devow
    
    jw_sim_deacc_devow = jw_safe(src_dd[2], tgt_dd[2])
    if DEBUG >= 2:
        print("jwsimdd: " + str(jw_sim_deacc_devow), file=sys.stderr)
    sim *= jw_sim_deacc_devow
    
    if DEBUG >= 2:
        print("sim    : " + str(sim), file=sys.stderr)
    return sim

if __name__ == "__main__":
    init(sys.argv[1], sys.argv[2])
    save_trtable(sys.argv[3]) # TODO
    # TODO print alignment

