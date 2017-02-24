#!/bin/bash

#set -o xtrace

s=$1
t=$2

if wget http://opus.lingfil.uu.se/OpenSubtitles2016/$s-$t.txt.zip
then
    set -e
    unzip $s-$t.txt.zip
    rm $s-$t.txt.zip OpenSubtitles2016.$s-$t.ids
    echo Para data downloaded successfully! >&2
    exit 0
elif wget http://opus.lingfil.uu.se/OpenSubtitles2016/$t-$s.txt.zip
then
    set -e
    unzip $t-$s.txt.zip
    mv OpenSubtitles2016.$t-$s.$s OpenSubtitles2016.$s-$t.$s
    mv OpenSubtitles2016.$t-$s.$t OpenSubtitles2016.$s-$t.$t
    rm $t-$s.txt.zip OpenSubtitles2016.$t-$s.ids
    echo Para data downloaded successfully! >&2
    exit 0
else
    echo No para data found! >&2
    exit 1
fi

