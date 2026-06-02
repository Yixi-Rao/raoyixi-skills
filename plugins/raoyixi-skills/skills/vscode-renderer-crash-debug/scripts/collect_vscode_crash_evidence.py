#!/usr/bin/env python3
"""Collect VS Code renderer crash evidence on macOS.

This script is intentionally read-only. It summarizes VS Code main/window logs,
Crashpad dumps, extension activation errors, and the active Copilot/Claude
state without printing secrets.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
from pathlib import Path


HOME = Path.home()
CODE_APP = Path("/Applications/Visual Studio Code.app")
CODE_CLI = CODE_APP / "Contents/Resources/app/bin/code"
CODE_USER = HOME / "Library/Application Support/Code"
LOGS_DIR = CODE_USER / "logs"
CRASHPAD_DIR = CODE_USER / "Crashpad/completed"
GLOBAL_STATE_DB = CODE_USER / "User/globalStorage/state.vscdb"
USER_EXTENSIONS = HOME / ".vscode/extensions"
DISABLED_EXTENSIONS = HOME / ".vscode/extensions-disabled"
DISABLED_BUILTIN = HOME / ".vscode/extensions-disabled-builtin"
BUILTIN_COPILOT = CODE_APP / "Contents/Resources/app/extensions/copilot"

SECRET_PATTERNS = [
    re.compile(r"(token|authorization|password|secret|api[_-]?key|auth[_-]?token)([\"'=:\s]+)([^,\s\"}]+)", re.I),
    re.compile(r"(raoyixi__)[A-Za-z0-9_./+-]+"),
    re.compile(r"eyJ[A-Za-z0-9_.-]+"),
]

ERROR_PATTERNS = [
    "renderer process gone",
    "CodeWindow: renderer process gone",
    "chatParticipant must be declared",
    "CopilotCLI",
    "GitHub.copilot-chat",
    "Anthropic.claude-code",
    "claude-code",
    "copilotcli",
    "copilot-cloud-agent",
    "Extension host terminating",
    "renderer closed the MessagePort",
    "FAILED to handle event",
    "lqyld.vscode-icons-iconify",
    "cliffordfajardo.hightlight-selections-vscode",
    "Failed to create database",
    "resolveAuthority",
    "An unknown error occurred",
]


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(lambda m: f"{m.group(1) if m.lastindex and m.lastindex >= 1 else ''}<REDACTED>", text)
    return text


def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return f"<failed: {exc}>"


def parse_cutoff(raw: str | None) -> dt.datetime | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return dt.datetime.strptime(raw, fmt)
        except ValueError:
            pass
    raise SystemExit(f"Invalid --since value: {raw!r}")


def mtime(path: Path) -> dt.datetime:
    return dt.datetime.fromtimestamp(path.stat().st_mtime)


def recent_files(root: Path, glob: str, since: dt.datetime | None) -> list[Path]:
    if not root.exists():
        return []
    files = list(root.glob(glob))
    if since:
        files = [p for p in files if mtime(p) >= since]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def log_files_since(since: dt.datetime | None) -> list[Path]:
    if not LOGS_DIR.exists():
        return []
    files = list(LOGS_DIR.glob("20*/**/*.log"))
    if since:
        files = [p for p in files if mtime(p) >= since]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def read_tail(path: Path, max_lines: int = 80) -> list[str]:
    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return []
    return lines[-max_lines:]


def grep_file(path: Path, patterns: list[str]) -> list[str]:
    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        return []
    out: list[str] = []
    lowered = [p.lower() for p in patterns]
    for index, line in enumerate(lines, start=1):
        if any(p in line.lower() for p in lowered):
            out.append(f"{path}:{index}: {redact(line)}")
    return out


def dump_strings(path: Path) -> list[str]:
    output = run(["strings", "-a", str(path)])
    keep = []
    for line in output.splitlines():
        if any(token in line for token in ["Code Helper", "Electron", "--type=renderer", "--vscode-window-config", "VSCODE_PID", "CachedData"]):
            keep.append(redact(line))
    return keep[:80]


def extension_versions() -> list[str]:
    if not CODE_CLI.exists():
        return []
    output = run([str(CODE_CLI), "--list-extensions", "--show-versions"])
    interesting = re.compile(r"(copilot|claude|anthropic|lqyld|clifford|hightlight|vscode-icons|remote-ssh)", re.I)
    return [line for line in output.splitlines() if interesting.search(line)]


def disabled_ids() -> list[str]:
    if not GLOBAL_STATE_DB.exists():
        return []
    try:
        with sqlite3.connect(GLOBAL_STATE_DB) as conn:
            row = conn.execute("select value from ItemTable where key='extensionsIdentifiers/disabled'").fetchone()
        if not row:
            return []
        data = json.loads(row[0])
        ids = [item.get("id", "") for item in data if isinstance(item, dict)]
        return sorted([x for x in ids if re.search(r"(copilot|claude|anthropic|lqyld|clifford|hightlight)", x, re.I)])
    except Exception as exc:  # noqa: BLE001
        return [f"<failed reading disabled ids: {exc}>"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect VS Code renderer crash evidence.")
    parser.add_argument("--since", help="Only emphasize files newer than this local time, e.g. '2026-06-02 17:00:00'.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    args = parser.parse_args()

    since = parse_cutoff(args.since)
    changed_log_files = log_files_since(since)
    main_logs = [p for p in changed_log_files if p.name == "main.log"]
    if not main_logs and LOGS_DIR.exists():
        main_logs = sorted(LOGS_DIR.glob("20*/main.log"), key=lambda p: p.stat().st_mtime)
    latest_main_log = main_logs[-1] if main_logs else None
    latest_log_dir = latest_main_log.parent if latest_main_log else None
    dumps = recent_files(CRASHPAD_DIR, "*.dmp", since)

    report: dict[str, object] = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "code_version": run([str(CODE_CLI), "--version"]) if CODE_CLI.exists() else "<code cli missing>",
        "latest_log_dir": str(latest_log_dir) if latest_log_dir else None,
        "crashpad_dumps": [{"path": str(p), "mtime": mtime(p).isoformat(timespec="seconds"), "strings": dump_strings(p)} for p in dumps[-10:]],
        "interesting_extensions": extension_versions(),
        "disabled_extension_ids": disabled_ids(),
        "builtin_copilot_present": BUILTIN_COPILOT.exists(),
        "disabled_builtin_copilot_dirs": [str(p) for p in sorted(DISABLED_BUILTIN.glob("*copilot*"))] if DISABLED_BUILTIN.exists() else [],
        "disabled_user_extension_dirs": [str(p) for p in sorted(DISABLED_EXTENSIONS.glob("*")) if re.search(r"(copilot|claude|anthropic|lqyld|clifford|hightlight)", p.name, re.I)] if DISABLED_EXTENSIONS.exists() else [],
        "main_log_tail": [],
        "key_log_hits": [],
    }

    if latest_log_dir and latest_main_log:
        report["main_log_tail"] = [redact(line) for line in read_tail(latest_main_log, 60)]
        hits: list[str] = []
        files_to_scan = changed_log_files if since else sorted(latest_log_dir.rglob("*.log"))
        for path in files_to_scan:
            hits.extend(grep_file(path, ERROR_PATTERNS))
        report["key_log_hits"] = hits[:500]

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print("# VS Code Renderer Crash Evidence")
    print(f"- generated_at: `{report['generated_at']}`")
    print(f"- latest_log_dir: `{report['latest_log_dir']}`")
    print(f"- builtin_copilot_present: `{report['builtin_copilot_present']}`")
    print("\n## Code Version\n")
    print("```")
    print(report["code_version"])
    print("```")
    print("\n## Crashpad Dumps\n")
    for item in report["crashpad_dumps"]:  # type: ignore[index]
        print(f"- `{item['mtime']}` `{item['path']}`")
        for line in item["strings"][:12]:
            print(f"  - `{line}`")
    print("\n## Interesting Extensions\n")
    for line in report["interesting_extensions"]:  # type: ignore[index]
        print(f"- `{line}`")
    print("\n## Disabled Extension IDs\n")
    for line in report["disabled_extension_ids"]:  # type: ignore[index]
        print(f"- `{line}`")
    print("\n## Main Log Tail\n")
    print("```")
    print("\n".join(report["main_log_tail"]))  # type: ignore[arg-type]
    print("```")
    print("\n## Key Log Hits\n")
    for line in report["key_log_hits"]:  # type: ignore[index]
        print(f"- {line}")


if __name__ == "__main__":
    main()
