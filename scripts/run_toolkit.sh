#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date -u +"%Y%m%dT%H%M%SZ")"

OUTDIR="$REPO_ROOT/outputs/$TS"
LATEST="$REPO_ROOT/latest"

mkdir -p "$OUTDIR" "$LATEST"

python3 "$REPO_ROOT/src/healthcheck.py" > "$OUTDIR/healthcheck.json"
python3 "$REPO_ROOT/src/logscan.py" --log "$REPO_ROOT/samples/auth_sample.log" > "$OUTDIR/logscan.json"

# convenience copies
cp "$OUTDIR/healthcheck.json" "$LATEST/healthcheck.json"
cp "$OUTDIR/logscan.json" "$LATEST/logscan.json"

echo "Wrote:"
echo "  $OUTDIR/healthcheck.json"
echo "  $OUTDIR/logscan.json"
echo "Latest:"
echo "  $LATEST/healthcheck.json"
echo "  $LATEST/logscan.json"
