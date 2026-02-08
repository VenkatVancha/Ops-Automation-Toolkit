#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"

OUTDIR="$REPO_ROOT/outputs/$TS"
LATEST="$REPO_ROOT/latest"

# Alert thresholds (tune later)
MAX_FAILED_AUTH_ATTEMPTS=10
MAX_ACCEPTED_PASSWORD=50

mkdir -p "$OUTDIR" "$LATEST"

HC_JSON="$OUTDIR/healthcheck.json"
LS_JSON="$OUTDIR/logscan.json"

# Run healthcheck
python3 "$REPO_ROOT/src/healthcheck.py" > "$HC_JSON"

# Run logscan against auth log (sudo if needed)
AUTH_LOG="/var/log/auth.log"
if [[ -r "$AUTH_LOG" ]]; then
  python3 "$REPO_ROOT/src/logscan.py" --log "$AUTH_LOG" > "$LS_JSON"
else
  sudo -n python3 "$REPO_ROOT/src/logscan.py" --log "$AUTH_LOG" > "$LS_JSON"
fi

# Convenience copies
cp "$HC_JSON" "$LATEST/healthcheck.json"
cp "$LS_JSON" "$LATEST/logscan.json"

# Extract health status + key metrics
HC_STATUS="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['overall_status'])")"
CPU="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['metrics']['cpu_percent'])")"
MEM="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['metrics']['memory']['percent_used'])")"
DISK="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['metrics']['disk']['percent_used'])")"

# Extract auth summary
FAILED_AUTH_TOTAL="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts'].get('failed_auth_attempts', 0))")"
FAILED_PASS="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts'].get('failed_password', 0))")"
FAILED_PUBKEY="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts'].get('failed_publickey', 0))")"
FAILED_PREAUTH="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts'].get('failed_preauth', 0))")"
INVALID_USER="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts'].get('invalid_user', 0))")"
ACCEPTED_PASS="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts'].get('accepted_password', 0))")"

ALERTS=0

# Health alert if warning/critical
if [[ "$HC_STATUS" != "OK" ]]; then
  ALERTS=1
fi

# Auth alert if failures exceed threshold
if (( FAILED_AUTH_TOTAL > MAX_FAILED_AUTH_ATTEMPTS )); then ALERTS=1; fi
if (( ACCEPTED_PASS > MAX_ACCEPTED_PASSWORD )); then ALERTS=1; fi

if (( ALERTS == 1 )); then
  echo "ALERT: toolkit run $TS"
  echo "Health: status=$HC_STATUS cpu=${CPU}% mem=${MEM}% disk=${DISK}%"
  echo "Auth: failed_total=$FAILED_AUTH_TOTAL (password=$FAILED_PASS publickey=$FAILED_PUBKEY preauth=$FAILED_PREAUTH invalid_user=$INVALID_USER) accepted_password=$ACCEPTED_PASS"
  echo "Wrote: $HC_JSON"
  echo "Wrote: $LS_JSON"
  echo "Latest: $LATEST/healthcheck.json, $LATEST/logscan.json"
else
  echo "OK: toolkit run $TS"
fi
