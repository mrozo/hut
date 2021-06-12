#!/usr/bin/env bash
. config.sh

function err() {
  echo "failed to send email $1, exit code: $2" >&2
}

for email_file in "${SOURCE_FOLDER}"/* ; do
  TITLE="$(head -n1 "${email_file}")"
  BODY="$(tail -n+2 "${email_file}")"
  EMAIL="$(basename "${email_file}")"
  swaks --auth \
    --server "${SMTP_SERVER}" \
    --from "${SENDER_EMAIL}" \
    --au "${SMTP_LOGIN}" \
    --ap "${SMTP_PASS}" \
    --to "${EMAIL}" \
    --tls \
    --h-Subject: "=?utf-8?B?$(echo "${TITLE}" | base64 -w0 -)?=" \
    --add-header "MIME-Version: 1.0" \
    --add-header "Content-Type: text/plain; charset=utf-8" \
    --body "${BODY}"

  retVal=$?
  if [ $retVal == 0 ] ; then
    rm "${email_file}"
  else
    err "${email_file}" $retVal
  fi;
done