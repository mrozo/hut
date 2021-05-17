#!/usr/bin/env bash
function print_help() {
  cat <<HELP_TEXT
Run tests for hut the HUT system.

Usage:
  $0 tests-path log-file

  when log-file is '-', redirect log to the stdout .
HELP_TEXT
}

function run_test() {
  COMMAND=$1
  TEST_FILE=$2

  $COMMAND "-if=${TEST_FILE}"
}

function test_skladkoinator() {
  SKLADKOINATOR_TESTS_PATH=$1
  TEST_COMMAND=$2
  TESTS_RESULT=0

  while read -r file; do
    echo "TESTING: ${file}"

    if ! $TEST_COMMAND "-if=${file}"; then
      echo "FAILED: ${file}"
      TESTS_RESULT=$((TESTS_RESULT + 1))
    else
      echo "PASSED: ${file}"
    fi
  done < <(find ./ -type f -path "${SKLADKOINATOR_TESTS_PATH}/*.dsv" )
  return $TESTS_RESULT
}


if [[ $# -lt 2 ]] ; then
  echo "no enough provided, usage:" >&2
  print_help;
  exit 1
fi

TESTS_PATH="$1"
[[ "${TESTS_PATH}" != */ ]] && TESTS_PATH="${TESTS_PATH}/"
LOG_FILE="$2"
if [[ "${LOG_FILE}" == "-" ]]; then
  LOG_FILE="&1"
fi;
TESTS_FAILED=0

function compare_dsv() {
  #that function is simplified, should be replaced with a field by field comparison
  A="$(echo -e "$1" | sed -r '/^\s*$/d')"
  B="$(echo -e "$2" | sed -r '/^\s*$/d')"
  if [[ "${A}" != "${B}" ]]; then
    return 1
  fi
  return 0
}

function test_parse_transactions() {
  TEST_FILE="$1"
  INPUT_MT940_FILE=""
  OUTPUT_DSV_FILE=""
  while read -r line; do
    if [[ $line == "EXPECTED DSV:" ]] ; then
      declare -n CURRENT_FILE=OUTPUT_DSV_FILE
    elif [[ $line == "INPUT MT940 FILE:" ]] ; then
      declare -n CURRENT_FILE=INPUT_MT940_FILE
    else
      CURRENT_FILE="${CURRENT_FILE}\n${line}"
    fi
  done < "${TEST_FILE}"

  TEST_RESULT="$(echo -e "${INPUT_MT940_FILE}" | ./parse_transactions.sh )"
  if compare_dsv "${TEST_RESULT}" "${OUTPUT_DSV_FILE}" ; then
    echo "PASSED: ${TEST_FILE}"
    return 0
  else
    echo "FAILED: ${TEST_FILE}"
    echo "Expected result:"
    echo -e "${OUTPUT_DSV_FILE}"
    echo "Actual result:"
    echo -e "${TEST_RESULT}"
    return 1
  fi;
}

test_skladkoinator "${TESTS_PATH}skladkoinator" "./skladkoinator.py" 1>"$LOG_FILE" 2>&1
TESTS_FAILED=$((TESTS_FAILED + $?))

while read -r file; do
  test_parse_transactions "${file}" 1>"$LOG_FILE" 2>&1
  TESTS_FAILED=$((TESTS_FAILED + $?))
done < <(find ./ -type f -path "${TESTS_PATH}parse_transactions/*.txt")

if [[ $TESTS_FAILED == 0 ]] ; then
  echo "ALL TESTS PASSED"
else
  echo "FAIL! Failed ${TESTS_FAILED} tests"
fi;
