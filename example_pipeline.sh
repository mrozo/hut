#!/usr/bin/env bash

if ! [ -f "${PWD}/"config.sh ] ; then
  echo "there is no 'config.sh' file in current working directory: ${PWD}" >&2
  exit 1
fi

. ./config.sh

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

mkdir -p "${OUT}"
mkdir -p "${EMAIL_TEMP_DIR}"

# calculate dues and generate monthly income/outcome report
"${SCRIPT_DIR}"/parse_transactions.sh $TRANSACTIONS | \
  tee >("${SCRIPT_DIR}"/classificator.py -if=- -of="${MONTHLY_REPORT}") | \
  "${SCRIPT_DIR}"/transactions2dues.py --hackers $HACKERS_FILE 2>$NOT_DUES_FILE | \
  cat $HOUSE_RULES - | sort | \
  "${SCRIPT_DIR}"/skladkoinator.py > "${DUES_REPORT}"

"${SCRIPT_DIR}"/mail_generator.py -if="${DUES_REPORT}" --output_dir="${EMAIL_TEMP_DIR}"

emails_count="$(ls -1 "${EMAIL_TEMP_DIR}")"

"${SCRIPT_DIR}"/email_sender.sh

not_sent_emails_count="$(ls -1 "${EMAIL_TEMP_DIR}" | wc -l)"
hackers_count="$(wc -l < "${HACKERS_FILE}")"
last_3_months_report="$(sort -r "${MONTHLY_REPORT}" | head -n3 )"

echo "
Hackers count: ${hackers_count}
Emails not sent: ${not_sent_emails_count}

Las three months income/outcome:
${last_3_months_report}
"
