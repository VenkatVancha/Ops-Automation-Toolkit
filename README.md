# Ops Automation Toolkit (Linux)

## Health Check (src/healthcheck.py)

Generates a JSON health snapshot for the current Linux system (works in WSL2).

**Includes**
- timezone-aware UTC timestamp
- host + OS info
- uptime (seconds)
- CPU usage percent (from `/proc/stat`)
- memory usage (from `/proc/meminfo`)
- disk usage for `/` (from `shutil.disk_usage`)
- simple status checks (OK/WARNING/CRITICAL) with thresholds

### Run
```bash
python3 src/healthcheck.py




## Log Scan (src/logscan.py)

Parses an auth log and outputs a JSON summary of SSH authentication events.

**Includes**
- failed password attempts
- invalid users
- accepted logins
- top source IPs and usernames

### Run (system auth log)
```bash
python3 src/logscan.py




## Run the Toolkit (scripts/run_toolkit.sh)

Runs the full toolkit and writes JSON outputs to a timestamped directoty.

### Run
```bash
./scripts/run_toolkit.sh




## Output Locations

- `outputs/<UTC_TIMESTAMP>/healthcheck.json`
- `outputs/<UTC_TIMESTAMP>/logscan.json`
- `latest/healthcheck.json` (most recent run)
- `latest/logscan.json` (most recent run)

