#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"

OUTDIR="$REPO_ROOT/outputs/$TS"
LATEST="$REPO_ROOT/latest"

# Alert thresholds (tune later)
MAX_FAILED_PASSWORD=10
MAX_INVALID_USER=5
MAX_ACCEPTED_PASSWORD=50

mkdir -p "$OUTDIR" "$LATEST"

HC_JSON="$OUTDIR/healthcheck.json"
LS_JSON="$OUTDIR/logscan.json"

# Run tools (write timestamped outputs)
python3 "$REPO_ROOT/src/healthcheck.py" > "$HC_JSON"
AUTH_LOG="/var/log/auth.log"

if [[ -r "$AUTH_LOG" ]]; then
  python3 "$REPO_ROOT/src/logscan.py" --log "$AUTH_LOG" > "$LS_JSON"
else
  sudo -n python3 "$REPO_ROOT/src/logscan.py" --log "$AUTH_LOG" > "$LS_JSON"
fi


# Convenience copies (most recent run)
cp "$HC_JSON" "$LATEST/healthcheck.json"
cp "$LS_JSON" "$LATEST/logscan.json"

# --- Alerting (quiet unless warning/critical or suspicious counts) ---

HC_STATUS="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['overall_status'])")"
CPU="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['metrics']['cpu_percent'])")"
MEM="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['metrics']['memory']['percent_used'])")"
DISK="$(python3 -c "import json; print(json.load(open('$HC_JSON'))['metrics']['disk']['percent_used'])")"

FAILED="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts']['failed_password'])")"
INVALID="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts']['invalid_user'])")"
ACCEPTED="$(python3 -c "import json; print(json.load(open('$LS_JSON'))['summary']['counts']['accepted_password'])")"

ALERTS=0

if [[ "$HC_STATUS" != "OK" ]]; then
  ALERTS=1
fi

if (( FAILED > MAX_FAILED_PASSWORD )); then ALERTS=1; fi
if (( INVALID > MAX_INVALID_USER )); then ALERTS=1; fi
if (( ACCEPTED > MAX_ACCEPTED_PASSWORD )); then ALERTS=1; fi

if (( ALERTS == 1 )); then
  echo "ALERT: toolkit run $TS"
  echo "Health: status=$HC_STATUS cpu=${CPU}% mem=${MEM}% disk=${DISK}%"
  echo "Auth: failed_password=$FAILED invalid_user=$INVALID accepted_password=$ACCEPTED"
  echo "Wrote: $HC_JSON"
  echo "Wrote: $LS_JSON"
  echo "Latest: $LATEST/healthcheck.json, $LATEST/logscan.json"
else
  echo "OK: toolkit run $TS"
fi

