#!/bin/bash

function fix_bnp_transactions_record () {
	if [[ -f "$1" ]] ; then
	    sed -e '/^:28C:.*\/M/s/\/\M//' $1
	else
	    exit 1
	fi
}

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

if [[ "$#" -lt 1 ]] ; then
    python3 mt940_parser.py;
    exit;
fi

for mt940_file in "$@" ; do
    fix_bnp_transactions_record "$mt940_file" | python3 mt940_2_dsv.py
done \
| sort | uniq

#!/bin/bash
print_help () {
    echo -e "Fix mt940 from bnp bank before parsing

\033[1mUsage:\033[0m   
\t$0 <input file>
"
} 


