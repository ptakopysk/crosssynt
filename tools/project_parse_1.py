#!/usr/bin/env python3
#coding: utf-8

import sys
from collections import defaultdict, Counter
import math

# TODO labelled

DEFAULT_PARENT = '0'
DEFAULT_PARENT_WEIGHT = -0.0000001

# 0
# 1: 1x tgt text
#    Nx src parse
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
        d[src].append(tgt)
    return d


with open(tgt_f) as tgt_fh:
    sent_len = [len(line.split()) for line in tgt_fh]


sent_pc_weight = defaultdict(lambda: defaultdict(int))

for src in range(N):
    sent = 0
    with open(alignment_f[src]) as alignment_fh, open(
            src_parse_f[src]) as src_parse_fh:
        src2tgt = align2dict(alignment_fh.readline())
        for line in src_parse_fh:
            line = line.strip()
            if line.startswith('#'):
                # comment
                pass
            elif not line:
                # end of sentence
                sent += 1
                src2tgt = align2dict(alignment_fh[src].readline())
            else:
                fields = line.split('\t')
                parent = fields[6]
                child = fields[0]
                if parent in src2tgt and child in src2tgt:
                    for tgt_parent in src2tgt[parent]:
                        for tgt_child in src2tgt[child]:
                            # - because MST computes MINIMUM spanning tree
                            sent_pc_weight[sent][(tgt_parent, tgt_child)] -= src_weights[i]
                            # TODO times alignment score

# add child->root edge for each child
for sent in sent_pc_weight:
    for child in range(1, sent_len[sent]+1):
        sent_pc_weight[sent][(DEFAULT_PARENT, child)] += DEFAULT_PARENT_WEIGHT


for sent in sent_pc_weight:
    print (sent_len[sent], *[" ".join([
        parent,
        child,
        str(sent_pc_weight[sent][(parent, child)])
        ])
            for (parent, child) in sent_pc_weight[sent]])

