#!/usr/bin/env python3
from datetime import datetime, date
from decimal import Decimal

from data_structures import Transaction, TransactionClassification
from dsv import dsv_reader, dsv_record_dump
from transactions2dues import is_due
from collections import OrderedDict
from typing import Iterable


def ERR(msg):
    raise Exception(msg)


def WARN(msg):
    sys.stderr.write(msg)
    sys.stderr.write("\n")


classificators = OrderedDict([
    (TransactionClassification.DUE, is_due),

    (TransactionClassification.OTHER_OUTCOME, lambda t: t.amount < 0),
    (TransactionClassification.OTHER_INCOME, lambda t: t.amount > 0),
    (TransactionClassification.UNKNOWN, lambda t: WARN(f"cannot classify transaction: {t}"))

])


def year_month(dt: datetime) -> date:
    return date(dt.year, dt.month, 1)


def classify_transaction(transaction: Transaction) -> (date, TransactionClassification, Decimal):
    for classification, classificator in classificators.items():
        if classificator(transaction):
            return year_month(transaction.date), classification, transaction.amount
    ERR(f"no classificator matched transaction: {transaction}")


def generate_monthly_report(transactions: Iterable[Transaction]):
    monthly_report = OrderedDict()
    for month, classification, amount in map(classify_transaction, transactions):
        if month not in monthly_report:
            monthly_report[month] = {}
        if classification not in monthly_report[month]:
            monthly_report[month][classification] = 0
        monthly_report[month][classification] += amount

    return monthly_report


def monthly_report_as_dsv(report: dict):
    for month in sorted(report.keys()):
        details = ""
        for classification, amount in report[month].items():
            details += f"{classification.value}={amount},"
        month_data = [
            month.isoformat(),
            details
        ]
        yield dsv_record_dump(month_data)
        yield "\n"


def classificator_main(input_file, output_file):
    transactions = map(lambda record: Transaction(*record), dsv_reader(input_file))
    monthly_report = generate_monthly_report(transactions)

    output_file.writelines(monthly_report_as_dsv(monthly_report))


if __name__ == "__main__":
    import argparse
    import sys

    hacker_cli_argparse = argparse.ArgumentParser()
    hacker_cli_argparse.add_argument("-if", action="store", dest="input_file", default="-", required=False)
    hacker_cli_argparse.add_argument("-of", action="store", dest="output_file", default="-", required=False)

    args = hacker_cli_argparse.parse_args()
    input_file = sys.stdin if args.input_file == '-' else open(args.input_file)
    output_file = sys.stdout if args.output_file == '-' else open(args.output_file, 'w')
    classificator_main(input_file, output_file)
