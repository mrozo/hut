#!/usr/bin/env bash

if [[ "$1" = "-h" || "$1" = "--help" ]] ; then
  echo"Convert XLS file with members list to a proper dsv members list.

  Arguments:
    - xls file path
    - optional output file path. If not provided result will be printed to stdout
  "
fi

TEMP_DIR="/tmp/$(basename "$0")_$(date | tr -s ' ,:' '_')"
mkdir "$TEMP_DIR"
libreoffice --headless --convert-to csv:"Text - txt - csv (StarCalc)":44,34,76 --outdir "${TEMP_DIR}" $1
CSV_FILE_PATH="${TEMP_DIR}/$(ls "$TEMP_DIR")"

CMD="cat \"$CSV_FILE_PATH\" | python3 ./czlonkowie_xls_2_hackers_dsv.py"
if [[ "$#" == 2 ]] ; then
  CMD="${CMD} > \"$2\""
fi

eval "${CMD}"
rm -rf "$TEMP_DIR"