#!/usr/bin/env python3
import sys
import mt940
import re
from sys import stderr
from datetime import datetime
from dsv import dsv_record_dump
import argparse
from typing import Iterable


def parse_desc_tag(desc_tag_contents):
    desc = {
        'transaction_code': '',
        'description': '',
        'additional_description': '',
        'subject': '',
        'contractors_bank_account': '',
        'contractors_account_number': '',
        'contractors_full_account_number': '',
        'contractors_address': ''
    }
    lines = desc_tag_contents.splitlines() + [None, ]
    desc['transaction_code'] = lines[0][0:3]
    lines[0] = lines[0][3:]
    l = lines[0]
    while l:
        if l.startswith('^00'):
            desc['description'] = re.match('[^^]{,27}', l[3:]).group().strip()
            l = lines.pop(0)
        elif l.startswith('^30'):
            desc['contractors_bank_account'] += l[3:].strip()
            l = lines.pop(0)
        elif l.startswith('^38'):
            desc['contractors_full_account_number'] = l[3:]
            l = lines.pop(0)
        elif l.startswith('^31'):
            desc['contractors_account_number'] = l[3:]
            l = lines.pop(0)
        elif re.match('^\^2[01234567]', l):
            l = l[3:]
            desc['subject'] += l[:27] 
            if len(l) > 27:
                l = l[27:]
            else:
                l = lines.pop(0)
        elif re.match('^\^6[23]', l):
            l = l[3:]
            desc['additional_description'] += l[:27] 
            if len(l) > 27:
                l = l[27:]
            else:
                l = lines.pop(0)
        elif re.match('^\^3[23]', l):
            l = l[3:]
            desc['contractors_address'] += l[:27] 
            if len(l) > 27:
                l = l[27:]
            else:
                l = lines.pop(0)
        else:
            stderr.write(f"filed to parse '{l}'")
            l=lines.pop(0)

    if 0 == len(desc['contractors_full_account_number']):
        desc['contractors_full_account_number'] = desc['contractors_bank_account'] + desc['contractors_account_number']

    return desc


def transaction_type(transaction_type_description):
    try:
        return {
            "C": "Credit",
            "RC": "Reversal credit",
            "D": "Debit",
            "RD": "Reversal Debit",
        }[transaction_type_description]
    except KeyError:
        return transaction_type_description


def format_date(date):
    return datetime(date.year, date.month, date.day, 0, 0, 0).isoformat()


def mt940_to_dsv(transactions: Iterable) -> Iterable[str]:
    for t in transactions:
        t = t.data
        desc = parse_desc_tag(t['transaction_details'])
        yield dsv_record_dump([
            format_date(t['entry_date']),
            t['extra_details'],
            desc['contractors_full_account_number'],
            desc['subject'],
            desc['contractors_address'],
            t['amount'].amount,
            t['amount'].currency,
            transaction_type(t['status']),
        ]) + "\n"


def parse_mt940(files: Iterable[str]) -> Iterable:
    handlers = []
    for file in files:
        handlers.append(sys.stdin if file == '-' else open(file, 'r'))

    for handler in handlers:
        yield from mt940.parse(handler)


if __name__ == "__main__":
    desc = f"""extract transactions from mt940 format to dsv.
\033[1mUsage:\033[0m
\t{sys.argv[0]} <source file>
\tcat <source file> | {sys.argv[0]}
  
\033[1mOutput format:\033[0m
\tOutput format is a DSV using colon ';' as the delimiter.

\t<transaction date>;<account number>;<subject>;<address>;<amount>;<currency>;<transaction type>

\twhere:
\t\t<transaction date> ISO 8601 date time without time zone
\t\t<extra data> string, should be transaction ID
\t\t<account number>
\t\t<subject> string
\t\t<address> string
\t\t<amount> decimal
\t\t<currency> string
\t\t<transaction type> Credit/Reversal Credit/Debit/Reversal Debit or other"""

    hacker_cli_argparse = argparse.ArgumentParser(description=desc)
    hacker_cli_argparse.add_argument("-if", action="store", nargs='+', dest="input_files", default="-", required=False)
    hacker_cli_argparse.add_argument("-of", action="store", dest="output_file", default="-", required=False)

    args = hacker_cli_argparse.parse_args()
    output_file = sys.stdout if args.output_file == '-' else open(args.output_file)

    output_file.writelines(mt940_to_dsv(parse_mt940(args.input_files)))


