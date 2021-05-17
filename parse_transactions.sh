#!/bin/bash

if [[ "$1" == "-h"  || "$1" == "--help" ]] ; then
    echo -e "
MT940 parser capable of conferting one or multiple sources into one DSV file.
For more informatin on the ooutput format check mt940_parser.py --help .

\033[1mUsage:\033[0m
\t$0 --help
\t$0 ./*.STA
\tcat <input file> | $0

Output format can be sorted by date using sort(1).
"
    exit;
fi

function fix_bnp_transactions_record () {
    # :28C:0668-2019/BPL -> :28C:0668/2019
    # :28C:12/2020/M -> :28C:12/2020
    sed -e '/^:28C:/{s/-/\//;s/\/[^0-9].*$//}'
}


if [[ "$#" -lt 1 ]] ; then
    fix_bnp_transactions_record | python3 mt940_2_dsv.py | sort | uniq
    exit;
fi

for mt940_file in "$@" ; do
    fix_bnp_transactions_record < "$mt940_file"  | python3 mt940_2_dsv.py
done \
| sort | uniq

