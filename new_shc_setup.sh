#!/bin/bash

if [ -n $1 ];
then
    echo "Usage: $0 SETUPNAME"
    echo "Known setup names: "
    cd templates;
    ls allsteps*
else
    s=$1

    mkdir -p run
    sed -e s/SSS/$1/ -e s/TTT/$2/ templates/header-SSS-TTT.shc > run/$s-$1-$2.shc
    cat templates/$s.shc >> run/$s-$1-$2.shc
    echo Created run script: run/$s-$1-$2.shc >&2
    echo -e "To submit it, simply use:\n\ncd run; qsub $s-$1-$2.shc\n" >&2

fi

