#!/usr/bin/env python3
import argparse
from typing import Mapping, AnyStr
from datetime import datetime
from typing import Iterable
from dsv import dsv_reader, dsv_record_dump
from decimal import Decimal
from functools import reduce


class UnknownEventException(Exception):
    pass

test_events_file = """
2019-02-01;newMember;hacker1;no comment
2019-02-01;newMember;hacker2;no comment
2019-02-01;newMember;hacker3;no comment
2019-02-01;newMember;hacker11;no comment
2020-01-01;dueSet;-1,hacker1;moving data from physical notepad to hut
2020-01-01;dueSet;0,hacker2;moving data from physical notepad to hut
2020-01-01;dueSet;3,hacker3;moving data from physical notepad to hut
2020-03-02;dueAdd,3,hacker2;hacker 2 bought a cnc machine for the hackerspace
2020-06-11;dueSet;0,hacker11;an old member has come back
2020-08-12;transaction;651,donation box,;income from the donation box
"""

#NOW = datetime.now


class Event:
    def __init__(self, date: [str or datetime], type: str, args_str: str, comment: str = None):
        self.date = date if isinstance(date, datetime) else datetime.fromisoformat(date)
        self.type = type
        self.args = list(map(lambda arg: arg.strip(), args_str.split(',')))
        self.comment = comment or ''

    def as_dsv(self):
        return dsv_record_dump([
            self.date, self.type, ','.join(self.args), self.comment
        ])

    def __str__(self):
        return self.as_dsv()

class AccountState:
    def __init__(self):
        self.transaction_events = []
        self.balance = Decimal(0)

    def register_transaction(self, transaction_event: Event):
        self.transaction_events.append(transaction_event)

    def get_balance(self):
        return reduce(lambda balance, transaction_event: balance + Decimal(transaction_event.args[0]),
                      self.transaction_events, self.balance)


class HouseRules:
    default_rate = Decimal(100)
    rates = {}

    def __getitem__(self, email: str):
        return self.rates.get(str, HouseRules.default_rate)

    def __setitem__(self, email: str, rate: Decimal):
        self.rates[email] = rate

    def __delitem__(self, email):
        del self.rates[email]

    def __str__(self):
        val = 'DuesRates {'
        for k in self.rates:
            val += f"{k}: {self.rates[k]}"
        val += '}'
        return val


class HackerDues:
    balance = Decimal(0)
    email = None

    def __init__(self, entry_date: datetime, email: AnyStr, balance: Decimal = 0):
        self.entry_date = entry_date
        self.balance = balance
        self.email = email

    def __str__(self):
        return f"{self.__class__.__name__}(email={self.email}, balance={self.balance})"

    def __repr__(self):
        return self.__str__()

    def to_dsv(self):
        return dsv_record_dump([self.email, self.balance])


class EventHandlers:

    @staticmethod
    def nextMonth(event:Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        for due_record in dues.values():
            due_record.balance -= 1

    @staticmethod
    def newMember(event:Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        hacker_email = event.args.pop()
        dues[hacker_email] = HackerDues(datetime.now(), hacker_email)

    @staticmethod
    def dueSet(event:Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        balance, hacker_email = event.args[0:2]
        dues[hacker_email].balance = Decimal(balance)

    @staticmethod
    def dueAdd(event:Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        balance, hacker_email = event.args[0:2]
        dues[hacker_email].balance += Decimal(balance)

    @staticmethod
    def transaction(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        amount, subject = Decimal(event.args[0]), event.args[1]
        if subject in dues:
            hacker_email = subject
            rate = rates[hacker_email]
            dues[hacker_email].balance += amount / rate
        account_balance.register_transaction(event)

    @staticmethod
    def setDefaultDue(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        HouseRules.default_rate = Decimal(event.args[0])

    @staticmethod
    def assertHackersExist(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules,
                                   account_balance: AccountState):
        hacker_emails = set(event.args)
        assert hacker_emails.issubset(set(dues.keys())), event.comment

    @staticmethod
    def assertDefaultDueRateEquals(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        expected_default_due_rate = Decimal(event.args[0])
        assert HouseRules.default_rate == expected_default_due_rate, event.comment

    @staticmethod
    def assertHackerDueBalanceEquals(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        hacker_email, expected_balance = event.args[0], Decimal(event.args[1])
        actual_balance = dues[hacker_email].balance
        assert actual_balance == expected_balance, f"expected_balance={expected_balance}, " \
                                                   f"actual_balance={actual_balance}, comment:{event.comment}"

    @staticmethod
    def assertHackerDueRateEquals(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        hacker_email, expected_due_rate = event.args[0], Decimal(event.args[0])
        assert rates[hacker_email] == expected_due_rate, event.comment

    @staticmethod
    def default(event: Event, *_):
        raise UnknownEventException(event.type)


hacker_cli_argparse = argparse.ArgumentParser()
hacker_cli_argparse.add_argument("-if", action="store", dest="input_file", default="-", required=False)
hacker_cli_argparse.add_argument("-of", action="store", dest="output_file", default="-", required=False)


def event_reader(event_source: Iterable[str]) -> Event:
    for event_data in dsv_reader(event_source):
        yield Event(*event_data)


if __name__ == "__main__":
    import sys
    args = hacker_cli_argparse.parse_args()
    input_file = sys.stdin if args.input_file == '-' else open(args.input_file)
    output_file = sys.stdout if args.output_file == '-' else open(args.output_file)
    events = event_reader(input_file)
    dues_rates = HouseRules()
    dues_record = {}
    account_balance = AccountState()
    try:
        for event in event_reader(input_file):
            event_handler = getattr(EventHandlers, event.type, EventHandlers.default)
            event_handler(event, dues_record, dues_rates, account_balance)
    except UnknownEventException as e:
        print(e)
        print(f"dues_record: {dues_record}\ndues_rates: {dues_rates}")

    for hacker_dues in dues_record.values():
        output_file.write(hacker_dues.to_dsv())
        output_file.write("\n")

    #print(f"account balance: {account_balance.get_balance()}")
