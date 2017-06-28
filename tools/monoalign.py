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

# usage: ./monoalign.py src_sentences tgt_sentences lextable,txt > # alignment.align

# add this to counts
# SMOOTH = 0.1

# importance of length match
# LENIMP = 0.2

# max number of translation options for a word
ALIGNED_WORDS = 15

DEBUG = 2

vowels = r"[aeiouy]"

counts_src = Counter()
counts_tgt = Counter()
cooccurences = Counter()
sentences_src = list()
sentences_tgt = list()

def init(srcfile, tgtfile):
    global cooccurences, sentences_src, sentences_tgt
    with open(srcfile, "r") as srcfile_f, open(tgtfile, "r") as tgtfile_f:
            srclines = srcfile_f.readlines()
            tgtlines = tgtfile_f.readlines()
            assert len(srclines) == len(tgtlines), "Para data must be same length"
            for sent_index in range(len(srclines)):
                sentences_src.append(srclines[sent_index].split())
                sentences_tgt.append(tgtlines[sent_index].split())
                for src_word in sentences_src[sent_index]:
                    counts_src[src_word] += 1
                    for tgt_word in sentences_tgt[sent_index]:
                        cooccurences[(src_word, tgt_word)] += 1
                for tgt_word in sentences_tgt[sent_index]:
                    counts_tgt[tgt_word] += 1
                        
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
    # return 1/(1 + LENIMP*abs(srclen-tgtlen))
    return 1/(1 + abs(srclen-tgtlen))

@lru_cache(maxsize=1024)
def relposition(position, length):
    if length == 1:
        return 0.5
    else:
        return position/(length-1)

def diagsim(sent_index, srcword_index, tgtword_index):
    return abs(relposition(srcword_index, len(sentences_src[sent_index]))
            - relposition(tgtword_index, len(sentences_tgt[sent_index])))


def dicesim(srcword, tgtword):
    return 2*cooccurences[(srcword,tgtword)] / (
            counts_src[srcword] + counts_tgt[tgtword])

# @lru_cache(maxsize=1024)
def simscore(sent_index, srcword_index, tgtword_index):
    srcword = sentences_src[sent_index][srcword_index]
    tgtword = sentences_tgt[sent_index][tgtword_index]
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
    if DEBUG >= 2:
        print("dicesim  : " + str(dice_sim), file=sys.stderr)
    sim *= dice_sim

    # TODO have to keep separate counts for that
    # dice_sim_deacc_devow = dicesim(src_dd[2], tgt_dd[2])
    # sim *= dice_sim_deacc_devow

    diag_sim = diagsim(sent_index, srcword_index, tgtword_index)
    if DEBUG >= 2:
        print("diagsim  : " + str(diag_sim), file=sys.stderr)
    sim *= diag_sim

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


alignment_src2tgt = list()
alignment_tgt2src = list()
alignment_word = defaultdict(Counter)

def align(sent_index):
    global alignment_src2tgt, alignment_tgt2src

    sent_src = sentences_src[sent_index]
    sent_tgt = sentences_tgt[sent_index]

    # compute alignment scores
    matrix = dict()
    for srcword_index in range(len(sent_src)):
        for tgtword_index in range(len(sent_tgt)):
            matrix[(srcword_index, tgtword_index)] = simscore(
                    sent_index, srcword_index, tgtword_index)

    # find alignment
    alignment_src2tgt.append([(-1,0) for x in range(len(sent_src))])
    alignment_tgt2src.append([(-1,0) for x in range(len(sent_tgt))])
    
    for (srcword_index, tgtword_index) in sorted(matrix, key=matrix.get, reverse=True):
        if (alignment_src2tgt[sent_index][srcword_index] == (-1,0)
                and alignment_tgt2src[sent_index][tgtword_index] == (-1,0)):
            score = matrix[(srcword_index,tgtword_index)]
            alignment_src2tgt[sent_index][srcword_index] = (tgtword_index,score)
            alignment_tgt2src[sent_index][tgtword_index] = (srcword_index,score)
            alignment_word[sent_src[srcword_index]][sent_tgt[tgtword_index]] += 1

def print_alignment(sent_index):
    print(sent_index)
    print(str(len(sentences_src[sent_index])) + " "
        + " ".join(sentences_src[sent_index]) + "  # "
        + " ".join([str(x+1) for (x,_) in alignment_src2tgt[sent_index]]) + "  # "
        + " ".join([str(x) for (_,x) in alignment_src2tgt[sent_index]]))
    print(str(len(sentences_tgt[sent_index])) + " "
        + " ".join(sentences_tgt[sent_index]) + "  # "
        + " ".join([str(x+1) for (x,_) in alignment_tgt2src[sent_index]]) + "  # "
        + " ".join([str(x) for (_,x) in alignment_tgt2src[sent_index]]))

# Produces Moses lex format
# Moses phrase table format:
# Ach ||| pravdepodobne ||| 0.000245278 0.0002059 0.000262536 0.0001978 ||| 0-0 ||| 4077 3809 1 ||| |||
# Moses lex table format:
# šľachetného šlechetného 0.4285714
def save_trtable(trtable_file):
    with open(trtable_file, "w") as trtable:
        for srcword in alignment_word:
            total = sum(alignment_word[srcword].values())
            for (tgtword,count) in alignment_word[srcword].most_common(ALIGNED_WORDS):
                print(" ".join([srcword, tgtword, str(count/total)]), file=trtable)

if __name__ == "__main__":
    init(sys.argv[1], sys.argv[2])
    for sent_index in range(len(sentences_src)):
        align(sent_index)
        print_alignment(sent_index)
        if DEBUG >= 1:
            print("aligned sent " + str(sent_index), file=sys.stderr)
    save_trtable(sys.argv[3])

