#!/bin/bash

./align_forms.pl cs_small.txt en_small.txt > en2cs_small.txt
./view_align.pl < en2cs_small.txt

