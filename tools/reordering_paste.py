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
        # +1 for empty line -- TODO may be missing at file end!!!
        for i in range(len(links)+1):
            scol1.append(col1.readline().rstrip())
            scol2.append(col2.readline().rstrip())
            scol3.append(col3.readline().rstrip())
        for i in range(len(links)):
            index = # TODO!!!
            print(scol1[index], end='\t')
            print(scol2[i],     end='\t')
            print(scol3[index], end='\n')
        print()


