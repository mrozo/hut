#!/usr/bin/env python3
import argparse
from typing import Mapping
from datetime import timedelta
from typing import Iterable

from data_structures import Event, HouseRules, HackerDues, AccountState, DuesHistoryRecord
from dsv import dsv_reader, dsv_generator
from decimal import Decimal
from functools import partial


class EventReaderException(Exception):
    pass


class UnknownEventException(Exception):
    def __init__(self,event_name: str):
        self.event_name = event_name

    def __str__(self):
        return f"{self.__class__.__name__}({self.event_name})"
    pass


ONE_MONTH = timedelta(days=30)


class EventHandlers:

    @staticmethod
    def setHackerDue(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Set due price for selected hacker
        Event args: due price, hacker email
        """
        rate = Decimal(event.args[0])
        hacker_email = event.args[1]
        rates[hacker_email] = rate

    @staticmethod
    def setMaxPrepaidDuesCount(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        count = int(event.args.pop())
        rates.max_prepaid_dues_count = count

    @staticmethod
    def nextMonth(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Decrement dues balance for all hackers.
        Event args: None
        """
        for due_record in dues.values():
            if event.date - due_record.entry_date > ONE_MONTH:
                due_record.balance -= 1

    @staticmethod
    def newMember(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Register new member with dues balance = 0
        Event args: email
        """
        hacker_email = event.args.pop()
        dues[hacker_email] = HackerDues(event.date, hacker_email)

    @staticmethod
    def dueSet(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Set dues balance to value for selected hacker
        Event args: dues balance, email
        """
        hacker_email, balance = event.args[0:2]
        dues[hacker_email].balance = Decimal(balance)

    @staticmethod
    def dueAdd(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Increase dues balance for selected hacker by value
        Event args: email, value
        """
        hacker_email, balance = event.args[0:2]
        dues[hacker_email].balance += Decimal(balance)

    @staticmethod
    def transaction(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Register a financial transaction
        Event args: amount, subject
        """
        amount, subject = Decimal(event.args[0]), event.args[1]
        if subject in dues:
            hacker_email = subject
            rate = rates[hacker_email]
            balance = dues[hacker_email].balance
            if balance < rates.max_prepaid_dues_count:
                new_balance = min(balance + amount / rate, rates.max_prepaid_dues_count)
                dues[hacker_email].balance = new_balance
            dues[hacker_email].dues_history.append(DuesHistoryRecord(
                event.date, dues[hacker_email].balance, amount
            ))
        account_balance.register_transaction(event)

    @staticmethod
    def setDefaultDue(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Set default dues rate
        Event args: dues rate
        """
        HouseRules.default_rate = Decimal(event.args[0])

    @staticmethod
    def assertHackersExist(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules,
                           account_balance: AccountState):
        """
        Check if list of registered hackers contain provided list of hackers
        Event args: list of emails
        """
        hacker_emails = set(event.args)
        assert hacker_emails.issubset(set(dues.keys())), event.comment

    @staticmethod
    def assertDefaultDueRateEquals(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Check if default due rate is equal to provided one
        Event args: expected due rate
        """
        expected_default_due_rate = Decimal(event.args[0])
        assert HouseRules.default_rate == expected_default_due_rate, event.comment

    @staticmethod
    def assertHackerDueBalanceEquals(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Check if dues balance for selected hacker is equal to expected value
        Event args: email, expected dues balance
        """
        hacker_email, expected_balance = event.args[0], Decimal(event.args[1])
        actual_balance = dues[hacker_email].balance
        assert actual_balance == expected_balance, f"expected_balance={expected_balance}, " \
                                                   f"actual_balance={actual_balance}, comment:{event.comment}"

    @staticmethod
    def assertHackerDueRateEquals(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
        """
        Check if dues rate for selected hacker is equal to expected value
        Event args: email, expected dues rate
        """
        hacker_email, expected_due_rate = event.args[0], Decimal(event.args[0])
        assert rates[hacker_email] == expected_due_rate, event.comment

    @staticmethod
    def default(event: Event, *_):
        raise UnknownEventException(event.type)


def is_line_not_empty(line: str):
    return len(line) != 0


def event_reader(event_source: Iterable[str]) -> Iterable[Event]:
    for event_data in filter(is_line_not_empty, dsv_reader(event_source)):
        try:
            yield Event(*event_data)
        except Exception as e:
            raise EventReaderException(f"failed to read event line: {event_data}:\n{e}")


def handle_event(event: Event, dues: Mapping[str, HackerDues], rates: HouseRules, account_balance: AccountState):
    try:
        return getattr(EventHandlers, event.type, EventHandlers.default)(event, dues, rates, account_balance)
    except Exception as exc:
        raise Exception(f"Exception '{exc}' happened during handling of event: {event.as_dsv()}")


if __name__ == "__main__":
    import sys

    hacker_cli_argparse = argparse.ArgumentParser()
    hacker_cli_argparse.add_argument("-if", action="store", dest="input_file", default="-", required=False)
    hacker_cli_argparse.add_argument("-of", action="store", dest="output_file", default="-", required=False)

    args = hacker_cli_argparse.parse_args()
    input_file = sys.stdin if args.input_file == '-' else open(args.input_file)
    output_file = sys.stdout if args.output_file == '-' else open(args.output_file, 'w')

    dues_rates = HouseRules()
    dues_record = {}
    account_balance = AccountState()
    event_handler = partial(handle_event, dues=dues_record, rates=dues_rates, account_balance=account_balance)
    list(map(event_handler, event_reader(input_file)))

    output_file.writelines(dsv_generator(dues_record.values()))
