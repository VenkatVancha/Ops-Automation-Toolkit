#!/usr/bin/env python3
import json
import os
import platform
import shutil
import socket
import time
from datetime import datetime, timezone


def utc_timestamp() -> str:
    # timezone-aware UTC timestamp (fixes DeprecationWarning for utcnow())
    return datetime.now(timezone.utc).isoformat()


def get_hostname() -> str:
    return socket.gethostname()


def get_os_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }


def read_first_line(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.readline().strip()


def get_uptime_seconds() -> float:
    # /proc/uptime: "<uptime_seconds> <idle_seconds>"
    uptime_line = read_first_line("/proc/uptime")
    uptime_seconds_str = uptime_line.split()[0]
    return float(uptime_seconds_str)


def get_disk_usage(path: str = "/") -> dict:
    total, used, free = shutil.disk_usage(path)
    percent_used = (used / total) * 100 if total else 0.0
    return {
        "path": path,
        "total_bytes": total,
        "used_bytes": used,
        "free_bytes": free,
        "percent_used": round(percent_used, 2),
    }


def parse_proc_stat_cpu_line(line: str) -> dict:
    # Example: cpu  3357 0 4313 1362393 0 0 0 0 0 0
    parts = line.split()
    if parts[0] != "cpu":
        raise ValueError("Unexpected /proc/stat format (cpu line missing).")

    values = list(map(int, parts[1:]))

    # CPU time fields (Linux):
    # user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
    user = values[0]
    nice = values[1]
    system = values[2]
    idle = values[3]
    iowait = values[4] if len(values) > 4 else 0
    irq = values[5] if len(values) > 5 else 0
    softirq = values[6] if len(values) > 6 else 0
    steal = values[7] if len(values) > 7 else 0

    idle_all = idle + iowait
    non_idle = user + nice + system + irq + softirq + steal
    total = idle_all + non_idle

    return {"total": total, "idle_all": idle_all}


def get_cpu_usage_percent(sample_delay_seconds: float = 0.2) -> float:
    # Read /proc/stat twice and compute usage over interval.
    first = parse_proc_stat_cpu_line(read_first_line("/proc/stat"))
    time.sleep(sample_delay_seconds)
    second = parse_proc_stat_cpu_line(read_first_line("/proc/stat"))

    total_delta = second["total"] - first["total"]
    idle_delta = second["idle_all"] - first["idle_all"]

    if total_delta <= 0:
        return 0.0

    usage = (total_delta - idle_delta) / total_delta * 100
    return round(usage, 2)


def parse_meminfo() -> dict:
    # Reads /proc/meminfo and returns keys in kB
    meminfo = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as f:
        for line in f:
            # Example: "MemTotal:       16384256 kB"
            key, rest = line.split(":", 1)
            value_str = rest.strip().split()[0]
            meminfo[key] = int(value_str)
    return meminfo


def get_memory_usage() -> dict:
    mi = parse_meminfo()

    # kB values
    total_kb = mi.get("MemTotal", 0)
    available_kb = mi.get("MemAvailable", 0)

    used_kb = max(total_kb - available_kb, 0)
    percent_used = (used_kb / total_kb) * 100 if total_kb else 0.0

    # Convert to bytes for consistency with disk usage
    kb_to_bytes = 1024
    return {
        "total_bytes": total_kb * kb_to_bytes,
        "available_bytes": available_kb * kb_to_bytes,
        "used_bytes": used_kb * kb_to_bytes,
        "percent_used": round(percent_used, 2),
    }


def evaluate_threshold(value: float, warn: float, crit: float) -> dict:
    # Simple, readable status system
    if value >= crit:
        status = "CRITICAL"
    elif value >= warn:
        status = "WARNING"
    else:
        status = "OK"

    return {"value": value, "status": status, "warn_at": warn, "crit_at": crit}


def build_healthcheck() -> dict:
    uptime_seconds = get_uptime_seconds()
    disk = get_disk_usage("/")
    cpu_percent = get_cpu_usage_percent()
    mem = get_memory_usage()

    # Default thresholds (you can tune later)
    thresholds = {
        "cpu_percent": {"warn": 80.0, "crit": 95.0},
        "mem_percent": {"warn": 80.0, "crit": 95.0},
        "disk_percent": {"warn": 80.0, "crit": 95.0},
    }

    checks = {
        "cpu": evaluate_threshold(cpu_percent, thresholds["cpu_percent"]["warn"], thresholds["cpu_percent"]["crit"]),
        "memory": evaluate_threshold(mem["percent_used"], thresholds["mem_percent"]["warn"], thresholds["mem_percent"]["crit"]),
        "disk": evaluate_threshold(disk["percent_used"], thresholds["disk_percent"]["warn"], thresholds["disk_percent"]["crit"]),
    }

    overall = "OK"
    for c in checks.values():
        if c["status"] == "CRITICAL":
            overall = "CRITICAL"
            break
        if c["status"] == "WARNING":
            overall = "WARNING"

    return {
        "timestamp_utc": utc_timestamp(),
        "host": get_hostname(),
        "os": get_os_info(),
        "uptime_seconds": uptime_seconds,
        "metrics": {
            "cpu_percent": cpu_percent,
            "memory": mem,
            "disk": disk,
        },
        "checks": checks,
        "overall_status": overall,
    }


def main() -> None:
    data = build_healthcheck()
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()

