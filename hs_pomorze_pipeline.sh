#!/usr/bin/env bash
HACKERS_FILE=data/hackers.dsv
HOUSE_RULES=data/house_rules.dsv
TRANSACTIONS=data/transactions/*
NOT_DUES_FILE=data/not_dues.dsv

./parse_transactions.sh $TRANSACTIONS | \
  ./transactions2dues.py --hackers $HACKERS_FILE 2>$NOT_DUES_FILE | \
  cat $HOUSE_RULES - | sort | \
  ./skladkoinator.py