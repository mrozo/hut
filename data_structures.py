from datetime import datetime
from decimal import Decimal
from enum import Enum
from functools import reduce
from typing import AnyStr, List
from dataclasses import dataclass
from datetime import datetime

from dsv import dsv_record_dump, dsv_record_load


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
        return dsv_record_dump([self.hid, self.nick, self.entry_date, self.email, self.name, self.last_name,
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
    max_prepaid_dues_count = float('inf')

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


@dataclass(frozen=True, order=True)
class DuesHistoryRecord:
    date: datetime
    dues_balance: Decimal
    transaction_amount: Decimal

    def __init__(self, date, dues_balance: Decimal, transaction_amount: Decimal):
        object.__setattr__(self, 'date', date if isinstance(date, datetime) else datetime.fromisoformat(date))
        object.__setattr__(self, 'transaction_amount',  transaction_amount)
        object.__setattr__(self, 'dues_balance', dues_balance)

    def as_dsv(self, delimiter=';') -> str:
        return dsv_record_dump([self.date, self.transaction_amount, self.dues_balance], delimiter=delimiter)

    @classmethod
    def from_dsv(cls, line: str, delimiter: str = ';'):
        return cls(*dsv_record_load(line, delimiter=delimiter))


class HackerDues:
    balance = Decimal(0)
    email = None
    dues_history: List[DuesHistoryRecord] = None

    def __init__(self, entry_date: datetime, email: AnyStr, balance: Decimal = 0):
        self.entry_date = entry_date
        self.balance = balance
        self.email = email
        self.dues_history = []

    def __str__(self):
        return f"{self.__class__.__name__}(email={self.email}, balance={self.balance})"

    def __repr__(self):
        return self.__str__()

    def as_dsv(self):
        record = [self.email, self.balance]
        record += list(map(lambda t: t.as_dsv(delimiter=','), self.dues_history))
        return dsv_record_dump(record)

    @classmethod
    def from_dsv(cls, line, delimiter=';'):
        record = dsv_record_load(line, delimiter)
        dues_record = cls(None, record[0], Decimal(record[1]))
        if len(record) > 2:
            dues_record.dues_history.extend(list(map(
                lambda r: DuesHistoryRecord.from_dsv(r, delimiter=','), record[2:]
            )))
        return dues_record


class AccountState:

    def __init__(self):
        self.transaction_events = []
        self.balance = Decimal(0)

    def register_transaction(self, transaction_event: Event):
        self.transaction_events.append(transaction_event)

    def get_balance(self):
        return reduce(lambda balance, transaction_event: balance + Decimal(transaction_event.args[0]),
                      self.transaction_events, self.balance)


@dataclass(order=True)
class Transaction:
    date: datetime
    extra_details: str
    contractor_account_number: str
    subject: str
    contractor_address: str
    amount: Decimal
    currency: str
    transaction_type: str

    def __init__(self, date, extra_details, contractor_account_number, subject, contractor_address, amount, currency, transaction_type ):
        self.date = date if isinstance(date, datetime) else datetime.fromisoformat(date)
        self.extra_details = extra_details
        self.contractor_account_number = contractor_account_number
        self.subject = subject
        self.contractor_address = contractor_address
        self.amount = Decimal(amount)
        self.currency = currency
        self.transaction_type = transaction_type


class TransactionClassification(Enum):
    DUE = "due"
    DONATION = "donation"
    OTHER_INCOME = "other_income"
    RENT_AND_MEDIA = "rent_and_media"
    OTHER_OUTCOME = "other_outcome"
    UNKNOWN = "unknown"