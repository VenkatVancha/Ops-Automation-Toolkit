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

