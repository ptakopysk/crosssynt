#!/usr/bin/env python3
#coding: utf-8

import sys
from collections import defaultdict, Counter
import math

# 0
# 1: 1x tgt text
#    Nx src parse: sequence of parent ords
#    Nx src-tgt alignment
#  +-Nx src weight

# parameters
tgt_f = sys.argv[1]
arg_groups = 3 if sys.argv[0].endswith('weighted.py') else 2
N = (len(sys.argv)-2)/arg_groups
assert N == int(N), "must have matching number of arguments"
N = int(N)
src_parse_f = sys.argv[2:N+2]
alignment_f = sys.argv[N+2:2*N+2]
if arg_groups == 2:
    src_weights = [1] * N
else:
    src_weights = [float(w) for w in sys.argv[2*N+2:]]

#            if alignment.count('\t'):
#                # last two elements are forward and backward alignment score
#                al_score *= math.exp(
#                        float(alignments.pop()) +
#                        float(alignments.pop()))
# return src-to-tgt dict
def align2dict(align):
    d = defaultdict(list)
    for st in align.split():
        (src, tgt) = st.split('-')
        # alignment is 0-based but ords are 1-based
        src = int(src)+1
        tgt = int(tgt)+1
        d[src].append(tgt)
    # root is always aligned to root
    d[0] = [0]
    return d

sent_len = list()
sent_pc_weight = list()
with open(tgt_f) as tgt_fh:
    for line in tgt_fh:
        sent_len.append(len(line.split()))
        sent_pc_weight.append(defaultdict(int))
SENTS = len(sent_len)

for src in range(N):
    with open(alignment_f[src]) as alignment_fh, open(
            src_parse_f[src]) as src_parse_fh:
        sent = -1
        for line, alignment in zip(src_parse_fh, alignment_fh):
            sent += 1
            src2tgt = align2dict(alignment)
            parents = [int(p) for p in line.split()]
            children = range(1, len(parents)+1)
            for parent, child in zip(parents, children):
                for tgt_parent in src2tgt[parent]:
                    for tgt_child in src2tgt[child]:
                        # - because MST computes MINIMUM spanning tree
                        sent_pc_weight[sent][(tgt_parent, tgt_child)] -= src_weights[src]
            

# add child->root edge for each child
for sent in range(SENTS):
    for child in range(1, sent_len[sent]+1):
        sent_pc_weight[sent][(0, child)] += 0


for sent in range(SENTS):
    print (sent_len[sent], *[" ".join((
        str(parent), str(child), str(sent_pc_weight[sent][(parent, child)]) ))
        for (parent, child) in sent_pc_weight[sent]])

