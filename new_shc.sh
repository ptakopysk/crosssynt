#!/bin/bash

mkdir -p run
sed -e s/SSS/$1/ -e s/TTT/$2/ all-SSS-TTT.shc > run/all-$1-$2.shc
