from datetime import datetime
from decimal import Decimal
from functools import reduce
from typing import AnyStr

from dsv import dsv_record_dump


class Hacker:
    fields = {'hid', 'nick', 'entry_date', 'email', 'name', 'last_name', 'groups'}

    def __init__(self, hid: str, nick: str, entry_date: str, email: str, name: str, last_name: str, groups: [set, str]):
        self.hid = hid
        self.nick = nick
        self.entry_date = entry_date
        self.email = email
        self.name = name
        self.last_name = last_name
        groups = groups or set()
        if isinstance(groups, str):
            groups = set(groups.split(','))
        self.groups = groups

    def as_dsv(self):
        return dsv_record_dump([self.nick, self.nick, self.entry_date, self.email, self.name, self.last_name,
                                ",".join(self.groups)])


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

    def as_dsv(self):
        return dsv_record_dump([self.email, self.balance])


class AccountState:
    def __init__(self):
        self.transaction_events = []
        self.balance = Decimal(0)

    def register_transaction(self, transaction_event: Event):
        self.transaction_events.append(transaction_event)

    def get_balance(self):
        return reduce(lambda balance, transaction_event: balance + Decimal(transaction_event.args[0]),
                      self.transaction_events, self.balance)