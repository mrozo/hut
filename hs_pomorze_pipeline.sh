#!/usr/bin/env bash
HACKERS_FILE="data/hackers.dsv"
HOUSE_RULES="data/house_rules.dsv"
TRANSACTIONS="data/transactions/*"
OUT="data/out"
NOT_DUES_FILE="${OUT}/not_dues.dsv"
MONTHLY_REPORT="${OUT}/monthly_report.dsv"
DUES_REPORT="${OUT}/membership_fees_report.dsv"

mkdir -p "${OUT}"

./parse_transactions.sh $TRANSACTIONS | \
  tee >(./classificator.py -if=- -of="${MONTHLY_REPORT}") | \
  ./transactions2dues.py --hackers $HACKERS_FILE 2>$NOT_DUES_FILE | \
  cat $HOUSE_RULES - | sort | \
  ./skladkoinator.py > "${DUES_REPORT}"

