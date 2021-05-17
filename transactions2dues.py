#!/usr/bin/env python3
import argparse
from hacker import hacker_reader
from collections import namedtuple
from typing import Iterable
from dsv import dsv_reader, dsv_generator, dsv_record_dump
from data_structures import Hacker, Event
import re
from datetime import datetime
from sys import stderr

Transaction = namedtuple("Transaction", ['date', 'extra_details', 'contractors_full_account_number', 'subject',
                                         'contractors_address', 'amount', 'currency', 'status'])

hacker_cli_argparse = argparse.ArgumentParser()
hacker_cli_argparse.add_argument("--hackers", action="store", dest="hackers_file", required=True)
hacker_cli_argparse.add_argument("-if", action="store", dest="input_file",  default="-", required=False)
hacker_cli_argparse.add_argument("-of", action="store", dest="output_file", default="-", required=False)


def ERR(transaction: Transaction):
    sys.stderr.write(str(transaction))
    sys.stderr.write("\n")

def parse_transactions(data_source: Iterable[list]):
    return map(lambda record: Transaction(*record), dsv_reader(data_source))


def is_due(transaction: Transaction) -> bool:
    subject = transaction.subject
    subject = subject.lower().strip()
    return bool(re.search('sk.adka?', subject))


polish_letters_translation_mapping = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ż": "z", "ź": "z"
})


def drop_polish_letters(s: str):
    return s.translate(polish_letters_translation_mapping)


def find_hacker_email(transaction: Transaction, hackers: Iterable[Hacker]) -> str:
    for hacker in hackers:
        name, last_name = drop_polish_letters(hacker.name.lower()), drop_polish_letters(hacker.last_name.lower())
        subject = drop_polish_letters(transaction.subject.lower())
        if name in subject and last_name in subject:
            return hacker.email

        contractors_address = drop_polish_letters(transaction.contractors_address.lower())
        if name in contractors_address and last_name in contractors_address:
            return hacker.email
    return ""


def transactios2dues_events(transactions: Iterable[Transaction], hackers: Iterable[Hacker]) -> Iterable[Event]:
    for t in transactions:
        if is_due(t):
            hacker_email = find_hacker_email(t, hackers)
            if hacker_email:
                yield Event(t.date, 'transaction', f"{t.amount},{hacker_email}", '')
            else:
                ERR(t)
        else:
            ERR(t)


def first_of_the_month_event_generator(start_date: datetime) -> Iterable[Event]:
    first_of_the_month = datetime(year=start_date.year, month=start_date.month, day=1)
    while True:
        yield Event(first_of_the_month.isoformat(), "nextMonth", '')
        if first_of_the_month.month == 12:
            first_of_the_month = datetime(year=first_of_the_month.year + 1, month=1, day=1)
        else:
            first_of_the_month = datetime(year=first_of_the_month.year, month=first_of_the_month.month + 1, day=1)


def hackers2events(hackers: Iterable[Hacker]) -> Iterable[Event]:
    for h in hackers:
        yield Event(h.entry_date, "newMember", h.email)


def events_generator(hacker_events: Iterable[Hacker], transaction_events: Iterable[Hacker]) -> Iterable[Event]:
    first_date = min(transaction_events[0].date, hacker_events[0].date)
    first_of_the_month_events = iter(first_of_the_month_event_generator(first_date))
    current_month_event = next(first_of_the_month_events)

    for e in sorted(transaction_events + hacker_events, key=lambda e: e.date):
        while e.date.month != current_month_event.date.month:
            yield current_month_event
            current_month_event = next(first_of_the_month_events)
        yield e


if __name__ == "__main__":
    import sys
    args = hacker_cli_argparse.parse_args()
    input_file = sys.stdin if args.input_file == '-' else open(args.input_file)
    output_file = sys.stdout if args.output_file == '-' else open(args.output_file, 'w')
    hackers_file = open(args.hackers_file)

    hackers = list(hacker_reader(hackers_file))
    transactions = parse_transactions(input_file)

    transaction_events = sorted(transactios2dues_events(transactions, hackers), key=lambda e: e.date)
    hacker_events = sorted(hackers2events(hackers), key=lambda e: e.date)

    output_file.writelines(dsv_generator(events_generator(hacker_events, transaction_events)))
