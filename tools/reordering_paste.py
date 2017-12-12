#!/usr/bin/env python3
#coding: utf-8

import sys

(fcol1, fcol2, fcol3, freorder) = (sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]) 
with open(fcol1) as col1, open(fcol2) as col2, open(fcol3) as col3, open(freorder) as reorder:
    for alignment in reorder:
        links = alignment.split();
        scol1 = list()
        scol2 = list()
        scol3 = list()
        i2o = dict()
        o2i = dict()
        for i in range(len(links)):
            # indices: source-target (I-O)
            (indexI, indexO) = links[i].split('-'); # TODO convert to number
            i2o[indexI] = indexO
            o2i[indexO] = indexI
            scol1.append(col1.readline().rstrip())
            scol2.append(col2.readline().rstrip())
            scol3.append(col3.readline().rstrip())
        # +1 for empty line -- TODO may be missing at file end!!!
        scol1.append(col1.readline().rstrip())
        scol2.append(col2.readline().rstrip())
        scol3.append(col3.readline().rstrip())
        for indexO in range(len(col2)-1):
            # TODO fix token number and parent number
            indexI = o2i[indexO]
            tcol1 = scol1[indexI].split('\t');
            tcol1[0] = indexO+1
            print(*tcol1, sep='\t', end='\t')
            print(scol2[indexO], end='\t')
            tcol3 = scol3[indexI].split('\t');
            tcol3[2] = i2o[tcol3[2])
            print(*tcol3, sep='\t', end='\t')
        print()


