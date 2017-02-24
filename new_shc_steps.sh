#!/bin/bash

mkdir -p run
sed -e s/SSS/$1/ -e s/TTT/$2/ templates/allsteps-SSS-TTT.shc > run/allsteps-$1-$2.shc
echo Created run script: run/allsteps-$1-$2.shc >&2
echo -e "To submit it, simply use:\n\ncd run; qsub allsteps-$1-$2.shc\n" >&2

