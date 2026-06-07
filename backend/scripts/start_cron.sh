#!/usr/bin/env bash
set -euo pipefail

CRON_LOCAL_TIMEZONE="${CRON_LOCAL_TIMEZONE:-${BRIDGE_SYNC_LOCAL_TIMEZONE:-America/Chicago}}"
ZONEINFO_PATH="/usr/share/zoneinfo/${CRON_LOCAL_TIMEZONE}"
PYTHON_BIN="${PYTHON_BIN:-python}"

if [ -f "${ZONEINFO_PATH}" ]; then
  ln -snf "${ZONEINFO_PATH}" /etc/localtime
  echo "${CRON_LOCAL_TIMEZONE}" > /etc/timezone
  export TZ="${CRON_LOCAL_TIMEZONE}"
else
  echo "ERROR: timezone ${CRON_LOCAL_TIMEZONE} not found; refusing to start cron with the container default timezone" >&2
  exit 1
fi

export CRON_LOCAL_TIMEZONE
export BRIDGE_SYNC_LOCAL_TIMEZONE="${BRIDGE_SYNC_LOCAL_TIMEZONE:-${CRON_LOCAL_TIMEZONE}}"

"${PYTHON_BIN}" /app/scripts/render_cron_env.py /tmp/cron-container-env.sh

{
  printf "ADMIN_USERNAME=%s\n" "${ADMIN_USERNAME:-}"
  printf "ADMIN_PASSWORD=%s\n" "${ADMIN_PASSWORD:-}"
  printf "APPLICATION_URL=%s\n" "${APPLICATION_URL:-}"
  printf "BRIDGE_TRIGGER=%s\n" "${BRIDGE_TRIGGER:-nightly_cron}"
  printf "OGM_TRIGGER=%s\n" "${OGM_TRIGGER:-nightly}"
  printf "OGM_NIGHTLY_CRON_ENABLED=%s\n" "${OGM_NIGHTLY_CRON_ENABLED:-false}"
  printf "PYTHON_BIN=%s\n" "${PYTHON_BIN}"
  cat /app/config/crontab
} | crontab -

exec cron -f
