#!/usr/bin/env python3
import argparse
import json
import os
import re
from datetime import datetime, timezone


DEFAULT_AUTH_LOG = "/var/log/auth.log"

# Ubuntu auth.log patterns (common SSH auth lines)
RE_FAILED_PASSWORD = re.compile(r"Failed password for (invalid user )?(?P<user>\S+) from (?P<ip>\S+)")
RE_ACCEPTED_PASSWORD = re.compile(r"Accepted password for (?P<user>\S+) from (?P<ip>\S+)")
RE_INVALID_USER = re.compile(r"Invalid user (?P<user>\S+) from (?P<ip>\S+)")


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_read_lines(path: str) -> list[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n") for line in f]
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Log file not found: {path}") from e
    except PermissionError as e:
        raise PermissionError(
            f"Permission denied reading: {path}. Try: sudo python3 src/logscan.py"
        ) from e


def bump(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def top_n(counter: dict[str, int], n: int) -> list[dict]:
    items = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return [{"key": k, "count": v} for k, v in items]


def scan_auth_log(lines: list[str]) -> dict:
    counts = {
        "failed_password": 0,
        "accepted_password": 0,
        "invalid_user": 0,
    }

    ips: dict[str, int] = {}
    users: dict[str, int] = {}

    for line in lines:
        m = RE_FAILED_PASSWORD.search(line)
        if m:
            counts["failed_password"] += 1
            bump(ips, m.group("ip"))
            bump(users, m.group("user"))
            continue

        m = RE_ACCEPTED_PASSWORD.search(line)
        if m:
            counts["accepted_password"] += 1
            bump(ips, m.group("ip"))
            bump(users, m.group("user"))
            continue

        m = RE_INVALID_USER.search(line)
        if m:
            counts["invalid_user"] += 1
            bump(ips, m.group("ip"))
            bump(users, m.group("user"))
            continue

    return {
        "counts": counts,
        "top": {
            "ips": top_n(ips, 10),
            "users": top_n(users, 10),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan Ubuntu auth.log and summarize SSH auth events (JSON output)."
    )
    parser.add_argument("--log", default=DEFAULT_AUTH_LOG, help=f"Log path (default: {DEFAULT_AUTH_LOG})")
    args = parser.parse_args()

    lines = safe_read_lines(args.log)
    summary = scan_auth_log(lines)

    out = {
        "timestamp_utc": utc_timestamp(),
        "log_path": os.path.abspath(args.log),
        "lines_scanned": len(lines),
        "summary": summary,
    }

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
