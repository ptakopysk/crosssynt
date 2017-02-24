#!/bin/bash

sed -e s/SSS/$1/ -e s/TTT/$2/ all-SSS-TTT.sh > all-$1-$2.sh
chmod a+x all-$1-$2.sh

