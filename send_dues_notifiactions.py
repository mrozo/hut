#!/bin/env python3
from sys import stderr, stdout, stdin
from data_structures import HackerDues, DuesHistoryRecord
from typing import Iterable


def create_email(record: HackerDues):
    def dues_table(dues_history: Iterable[DuesHistoryRecord]):
        header = "{0:<20} | {1:^10} | {2:>24}".format("Data", "Wartość", "Saldo składek po wpłacie")
        yield header
        yield '-' * len(header)
        for r in dues_history:
            yield "{0:<20} | {1:>10} | {2:>24}".format(r.date, r.transaction_amount, r.dues_balance)
        yield '-' * len(header)

    return f"""Cześć,
twoje aktualne saldo składek w stowarzyszeniu hackerspace pomorze to: {record.balance}.

Historia wpłat:
""" + '\n'.join(dues_table(record.dues_history))


def send_email(subject, body, to):


if __name__ == "__main__":
    input_file = stdin
    output_file = stdout

    records = map(HackerDues.from_dsv, input_file)
    emails = map(create_email, records)

    for email in emails:
        print(email)
        print('-' * 80)
