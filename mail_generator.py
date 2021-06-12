#!/usr/bin/env python3

import argparse
from data_structures import HackerDues
from decimal import Decimal
from enum import Enum
from pathlib import Path


class EmailSubject(Enum):
    NEGATIVE_BALANCE = "Przypomnienie o składkach"
    NON_NEGATIVE_BALANCE = "Twoje składki"


EMAIL_TEMPLATE = \
    r"""{subject}

Witaj twój aktualny balans składek członkowskich w stowarzyszeniu hackerspace pomorze wynosi: {balance}.

Lista Twoich składek:
 L.P. |      data       | Wpłata | Balans składek
{dues_list}

Jeśli na liście składek brakuje jakiś wpłat, to sprawdź czy tutuł wysłanego przelewu zgadza się z formatem zdefiniowanym na wiki: https://wiki.hsp.sh/membership#dane_do_przelewu i skontaktuj się z zarządem: https://wiki.hsp.sh/zarzad . 

Buziaczki
składkoinator
"""

DUES_LIST_TEMPLATE = r"""{index:<5} | {date:^15} | {balance:>6} | {amount:>14}"""


def get_subject(dues_balance: Decimal) -> str:
    if dues_balance < 0:
        return EmailSubject.NEGATIVE_BALANCE.value
    return EmailSubject.NON_NEGATIVE_BALANCE.value


def generate_email(hacker_dues: HackerDues) -> str:
    dues_list_records = map(lambda index, due_history_record: {
        "index": index,
        "date": due_history_record.date.date().isoformat(),
        "amount": due_history_record.transaction_amount,
        "balance": due_history_record.dues_balance
        },
        range(len(hacker_dues.dues_history), 0, -1),
        sorted(hacker_dues.dues_history, reverse=True,  key=lambda x: x.date))
    dues_list = '\n'.join(map(lambda dues_record: DUES_LIST_TEMPLATE.format(**dues_record), dues_list_records))
    args = dict(
        subject=get_subject(hacker_dues.balance),
        balance=hacker_dues.balance,
        dues_list=dues_list)

    return EMAIL_TEMPLATE.format(**args)


if __name__ == "__main__":
    import sys

    hacker_cli_argparse = argparse.ArgumentParser()
    hacker_cli_argparse.add_argument("-if", action="store", dest="input_file", default="-", required=False)
    hacker_cli_argparse.add_argument("--output_dir", action="store", dest="output_dir", default=".", required=False)

    args = hacker_cli_argparse.parse_args()
    input_file = sys.stdin if args.input_file == '-' else open(args.input_file)
    output_dir = Path(args.output_dir)

    for hacker_dues in map(HackerDues.from_dsv, input_file):
        with open(output_dir / hacker_dues.email, 'w') as output_file:
            output_file.write(generate_email(hacker_dues))
