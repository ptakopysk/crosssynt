#!/usr/bin/env python3
#coding: utf-8

import sys
import monotranslate

monotranslate.init(sys.argv[1], sys.argv[2])
monotranslate.DEBUG = 0

sumscore = 0
countlines = 0
for line in sys.stdin:
    line = line.rstrip('\n')
    if line != '' and not line.startswith('#'):
        fields = line.split('\t')
        (fields[1], score) = monotranslate.translatecased(fields[1])
        sumscore += score
        countlines += 1
        print('\t'.join(fields))
    else:
        print(line)
print("avgscore: " + str(sumscore/countlines), file=sys.stderr)

