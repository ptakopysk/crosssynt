#!/bin/bash

mkdir -p run
sed -e s/SSS/$1/ -e s/TTT/$2/ all-SSS-TTT.shc > run/all-$1-$2.shc
echo Created run script: run/all-$1-$2.shc >&2
echo -e "To submit it, simply use:\n\nqsub run/all-$1-$2.shc\n" >&2

