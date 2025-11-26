#!/usr/bin/env bash
set -eo pipefail

BOT_TOKEN="8356603237:AAFrMgKbnfYsakMhJlIGc6tBrGWxB8Ix-vY"
CHAT_ID="505555650"

# Allow overriding chat ID via first argument if env not set
if [[ $# -ge 1 && -z "$CHAT_ID" ]]; then
  CHAT_ID="$1"
  shift
fi

MESSAGE=${1:-"Fall"}

if [[ -z "$BOT_TOKEN" ]]; then
  echo "Set TELEGRAM_BOT_TOKEN (env) before running." >&2
  exit 1
fi

if [[ -z "$CHAT_ID" ]]; then
  echo "Provide TELEGRAM_CHAT_ID (env) or as first argument." >&2
  exit 1
fi

curl -sS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "text=${MESSAGE}" \
  -H 'Content-Type: application/x-www-form-urlencoded'
