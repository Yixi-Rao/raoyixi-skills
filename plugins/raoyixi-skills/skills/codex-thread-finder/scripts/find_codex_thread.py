#!/usr/bin/env python3
"""Find the most active Codex thread across local and Remote SSH homes."""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import shlex
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


REMOTE_SCAN_CODE = r'''
import datetime as dt, glob, json, os, re, sqlite3, sys
from pathlib import Path

payload = json.loads(sys.argv[1])
START = float(payload["start"])
END = float(payload["end"])

def parse_ts(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value) / 1000.0 if value > 10_000_000_000 else float(value)
    if not isinstance(value, str):
        return None
    try:
        text = value.replace("Z", "+00:00")
        return dt.datetime.fromisoformat(text).timestamp()
    except Exception:
        return None

def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None

def thread_id_from_path(path):
    m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", str(path))
    return m.group(1) if m else None

def user_message(payload):
    if not isinstance(payload, dict):
        return False
    if payload.get("type") == "message" and payload.get("role") == "user":
        return True
    inner = payload.get("payload")
    return isinstance(inner, dict) and inner.get("type") == "message" and inner.get("role") == "user"

def scan_rollout(path):
    tid = None
    cwd = ""
    user_count = 0
    event_count = 0
    last_user_ts = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                event_count += 1
                if obj.get("type") == "session_meta":
                    meta = obj.get("payload") or {}
                    tid = meta.get("id") or tid
                    cwd = meta.get("cwd") or cwd
                if obj.get("type") != "response_item":
                    continue
                payload = obj.get("payload") or {}
                if not user_message(payload):
                    continue
                ts = parse_ts(obj.get("timestamp"))
                if ts is None or START <= ts <= END:
                    user_count += 1
                    last_user_ts = max(last_user_ts or ts or 0, ts or 0)
    except Exception as exc:
        return None, str(exc)
    tid = tid or thread_id_from_path(path)
    if not tid or user_count == 0:
        return None, None
    return {
        "thread_id": tid,
        "user_count": user_count,
        "event_count": event_count,
        "last_user_ts": last_user_ts,
        "cwd": cwd,
        "rollout_path": str(path),
        "evidence": "session_jsonl",
    }, None

def read_sqlite_threads(home):
    result = {}
    db = Path(home) / "state_5.sqlite"
    if not db.exists():
        return result
    try:
        con = sqlite3.connect(str(db))
        con.row_factory = sqlite3.Row
        rows = con.execute("select * from threads").fetchall()
        for row in rows:
            result[row["id"]] = dict(row)
    except Exception:
        pass
    return result

def read_session_index(home):
    result = {}
    path = Path(home) / "session_index.jsonl"
    if not path.exists():
        return result
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                tid = obj.get("id")
                if tid:
                    result[tid] = obj
    except Exception:
        pass
    return result

def discover_homes():
    homes = []
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        homes.append(env_home)
    for env_path in glob.glob("/proc/[0-9]*/environ"):
        try:
            raw = Path(env_path).read_bytes()
            if b"CODEX_HOME=" in raw:
                for part in raw.split(b"\0"):
                    if part.startswith(b"CODEX_HOME="):
                        homes.append(part.split(b"=", 1)[1].decode("utf-8", "ignore"))
        except Exception:
            continue
    homes.extend(glob.glob("/lpai/.codex-*-home"))
    homes.extend(glob.glob("/lpai/*/.codex/home"))
    homes.append(str(Path.home() / ".codex"))
    homes.append("/root/.codex")
    seen = []
    for home in homes:
        if not home:
            continue
        p = Path(home).expanduser()
        try:
            s = str(p.resolve())
        except Exception:
            s = str(p)
        if s not in seen and p.exists():
            seen.append(s)
    return seen

def scan_home(home):
    meta = read_sqlite_threads(home)
    index = read_session_index(home)
    candidates = {}
    errors = []
    for path in glob.glob(str(Path(home) / "sessions" / "**" / "rollout-*.jsonl"), recursive=True):
        item, err = scan_rollout(path)
        if err:
            errors.append({"path": path, "error": err})
        if not item:
            continue
        tid = item["thread_id"]
        row = meta.get(tid, {})
        idx = index.get(tid, {})
        item["title"] = row.get("title") or idx.get("thread_name") or ""
        item["cwd"] = item.get("cwd") or row.get("cwd") or ""
        item["source"] = "remote-ssh"
        item["codex_home"] = home
        candidates[tid] = item
    return list(candidates.values()), errors

all_candidates = []
all_errors = []
homes = discover_homes()
for home in homes:
    cands, errs = scan_home(home)
    all_candidates.extend(cands)
    all_errors.extend(errs[:20])
print(json.dumps({"homes": homes, "candidates": all_candidates, "errors": all_errors}, ensure_ascii=False))
'''

REMOTE_CONTENT_CODE = r'''
import datetime as dt, json, re, sys

payload = json.loads(sys.argv[1])
PATH = payload["path"]
START = float(payload["start"])
END = float(payload["end"])
SCOPE = payload["scope"]
MAX_CHARS = int(payload["max_chars"])

SECRET_RE = re.compile(r"(?i)(token|secret|password|authorization|credential|api[_-]?key|private[_-]?key)(\s*[:=]\s*)([^\s,;]+)")

def parse_ts(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value) / 1000.0 if value > 10_000_000_000 else float(value)
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None

def redact(text):
    return SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + "<redacted>", text)

def content_text(content):
    if isinstance(content, str):
        return content
    parts = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "input_text", "output_text"):
                    val = item.get(key)
                    if isinstance(val, str):
                        parts.append(val)
    elif isinstance(content, dict):
        for key in ("text", "input_text", "output_text"):
            val = content.get(key)
            if isinstance(val, str):
                parts.append(val)
    return "\n".join(parts)

messages = []
with open(PATH, "r", encoding="utf-8") as f:
    for line in f:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") != "response_item":
            continue
        msg = obj.get("payload") or {}
        if msg.get("type") != "message" or msg.get("role") not in ("user", "assistant"):
            continue
        ts = parse_ts(obj.get("timestamp"))
        if SCOPE == "range" and (ts is None or not (START <= ts <= END)):
            continue
        text = redact(content_text(msg.get("content")))
        truncated = False
        if MAX_CHARS > 0 and len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n...[truncated]"
            truncated = True
        messages.append({"timestamp": obj.get("timestamp"), "role": msg.get("role"), "text": text, "truncated": truncated})
print(json.dumps({"messages": messages}, ensure_ascii=False))
'''


def local_tz(name: str) -> dt.tzinfo:
    if ZoneInfo:
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    return dt.timezone(dt.timedelta(hours=8))


def parse_time(value: str, *, is_end: bool, tz: dt.tzinfo) -> float:
    text = value.strip()
    date_only = bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", text))
    if date_only:
        base = dt.datetime.fromisoformat(text).replace(tzinfo=tz)
        if is_end:
            base = base + dt.timedelta(days=1) - dt.timedelta(microseconds=1)
        return base.timestamp()
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    if text.endswith("Z"):
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    else:
        parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    return parsed.timestamp()


def iso(ts: Optional[float]) -> str:
    if not ts:
        return ""
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Optional[Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def parse_event_ts(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) / 1000.0 if value > 10_000_000_000 else float(value)
    if not isinstance(value, str):
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def thread_id_from_path(path: Path) -> Optional[str]:
    match = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", str(path))
    return match.group(1) if match else None


def is_user_response_item(obj: Dict[str, Any]) -> bool:
    if obj.get("type") != "response_item":
        return False
    payload = obj.get("payload") or {}
    return payload.get("type") == "message" and payload.get("role") == "user"


SECRET_RE = re.compile(r"(?i)(token|secret|password|authorization|credential|api[_-]?key|private[_-]?key)(\s*[:=]\s*)([^\s,;]+)")


def redact_text(text: str) -> str:
    return SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + "<redacted>", text)


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    parts: List[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "input_text", "output_text"):
                    value = item.get(key)
                    if isinstance(value, str):
                        parts.append(value)
    elif isinstance(content, dict):
        for key in ("text", "input_text", "output_text"):
            value = content.get(key)
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts)


def scan_rollout(path: Path, start: float, end: float) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    tid = None
    cwd = ""
    user_count = 0
    event_count = 0
    last_user_ts = None
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                event_count += 1
                if obj.get("type") == "session_meta":
                    meta = obj.get("payload") or {}
                    tid = meta.get("id") or tid
                    cwd = meta.get("cwd") or cwd
                if not is_user_response_item(obj):
                    continue
                ts = parse_event_ts(obj.get("timestamp"))
                if ts is not None and start <= ts <= end:
                    user_count += 1
                    last_user_ts = max(last_user_ts or ts, ts)
    except Exception as exc:
        return None, str(exc)
    tid = tid or thread_id_from_path(path)
    if not tid or user_count == 0:
        return None, None
    return {
        "thread_id": tid,
        "source": "local",
        "user_count": user_count,
        "event_count": event_count,
        "last_user_ts": last_user_ts,
        "cwd": cwd,
        "rollout_path": str(path),
        "evidence": "session_jsonl",
    }, None


def extract_local_content(path: Path, start: float, end: float, scope: str, max_chars: int) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("type") != "response_item":
                continue
            msg = obj.get("payload") or {}
            if msg.get("type") != "message" or msg.get("role") not in ("user", "assistant"):
                continue
            ts = parse_event_ts(obj.get("timestamp"))
            if scope == "range" and (ts is None or not (start <= ts <= end)):
                continue
            text = redact_text(content_to_text(msg.get("content")))
            truncated = False
            if max_chars > 0 and len(text) > max_chars:
                text = text[:max_chars] + "\n...[truncated]"
                truncated = True
            messages.append({
                "timestamp": obj.get("timestamp"),
                "role": msg.get("role"),
                "text": text,
                "truncated": truncated,
            })
    return messages


def read_sqlite_threads(home: Path) -> Dict[str, Dict[str, Any]]:
    db = home / "state_5.sqlite"
    result: Dict[str, Dict[str, Any]] = {}
    if not db.exists():
        return result
    try:
        con = sqlite3.connect(str(db))
        con.row_factory = sqlite3.Row
        for row in con.execute("select * from threads"):
            result[row["id"]] = dict(row)
    except Exception:
        return result
    return result


def read_session_index(home: Path) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    path = home / "session_index.jsonl"
    if not path.exists():
        return result
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    item = json.loads(line)
                except Exception:
                    continue
                tid = item.get("id")
                if tid:
                    result[tid] = item
    except Exception:
        pass
    return result


def scan_local(home: Path, start: float, end: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    meta = read_sqlite_threads(home)
    index = read_session_index(home)
    candidates: Dict[str, Dict[str, Any]] = {}
    errors = []
    for raw in glob.glob(str(home / "sessions" / "**" / "rollout-*.jsonl"), recursive=True):
        path = Path(raw)
        item, err = scan_rollout(path, start, end)
        if err:
            errors.append({"path": str(path), "error": err})
        if not item:
            continue
        tid = item["thread_id"]
        row = meta.get(tid, {})
        idx = index.get(tid, {})
        item["title"] = row.get("title") or idx.get("thread_name") or ""
        item["cwd"] = item.get("cwd") or row.get("cwd") or ""
        item["codex_home"] = str(home)
        candidates[tid] = item
    return list(candidates.values()), errors


def load_global_state(home: Path) -> Dict[str, Any]:
    return read_json(home / ".codex-global-state.json") or {}


def remote_maps(state: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, str]]:
    connections = {
        item.get("hostId"): item
        for item in state.get("codex-managed-remote-connections", [])
        if isinstance(item, dict) and item.get("hostId")
    }
    projects = {
        item.get("id"): item
        for item in state.get("remote-projects", [])
        if isinstance(item, dict) and item.get("id")
    }
    assignments = state.get("thread-project-assignments", {})
    if not isinstance(assignments, dict):
        assignments = {}
    return connections, projects, assignments


def prompt_history_candidates(state: Dict[str, Any], connections: Dict[str, Dict[str, Any]], projects: Dict[str, Dict[str, Any]], assignments: Dict[str, str]) -> List[Dict[str, Any]]:
    prompt_history = ((state.get("electron-persisted-atom-state") or {}).get("prompt-history") or {})
    if not isinstance(prompt_history, dict):
        return []
    result = []
    for tid, prompts in prompt_history.items():
        if tid == "global" or not isinstance(prompts, list) or not prompts:
            continue
        project_id = assignments.get(tid)
        project = projects.get(project_id, {})
        host_id = project.get("hostId")
        conn = connections.get(host_id, {})
        source = "remote-ssh-prompt-history" if host_id else "local-prompt-history"
        result.append({
            "thread_id": tid,
            "source": source,
            "remote_alias": conn.get("alias") or conn.get("displayName") or host_id or "",
            "remote_host_id": host_id or "",
            "remote_project_id": project_id or "",
            "remote_path": project.get("remotePath") or "",
            "user_count": len(prompts),
            "event_count": len(prompts),
            "last_user_ts": None,
            "title": "",
            "cwd": project.get("remotePath") or "",
            "rollout_path": "",
            "evidence": "prompt_history_no_timestamps",
        })
    return result


def ssh_probe(alias: str, timeout: int) -> Tuple[bool, str]:
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}", alias, "printf ok"]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout + 5)
    except Exception as exc:
        return False, str(exc)
    if proc.returncode == 0 and proc.stdout.strip() == "ok":
        return True, ""
    return False, (proc.stderr or proc.stdout).strip()


def scan_remote(alias: str, host_id: str, timeout: int, start: float, end: float) -> Dict[str, Any]:
    ok, err = ssh_probe(alias, timeout)
    diag: Dict[str, Any] = {"alias": alias, "host_id": host_id, "ok": ok}
    if not ok:
        diag["error"] = err
        diag["candidates"] = []
        return diag
    payload = json.dumps({"start": start, "end": end}, ensure_ascii=False)
    remote_cmd = "python3 -c " + shlex.quote(REMOTE_SCAN_CODE) + " " + shlex.quote(payload)
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}", alias, remote_cmd]
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=max(20, timeout + 20))
    except Exception as exc:
        diag.update({"ok": False, "error": f"remote scan failed: {exc}", "candidates": []})
        return diag
    if proc.returncode != 0:
        diag.update({"ok": False, "error": (proc.stderr or proc.stdout).strip(), "candidates": []})
        return diag
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        diag.update({"ok": False, "error": f"invalid remote JSON: {exc}", "raw": proc.stdout[-500:], "candidates": []})
        return diag
    candidates = data.get("candidates") or []
    for item in candidates:
        item["source"] = "remote-ssh"
        item["remote_alias"] = alias
        item["remote_host_id"] = host_id
    diag.update({"homes": data.get("homes") or [], "errors": data.get("errors") or [], "candidates": candidates})
    return diag


def extract_remote_content(alias: str, path: str, timeout: int, start: float, end: float, scope: str, max_chars: int) -> List[Dict[str, Any]]:
    payload = json.dumps({"path": path, "start": start, "end": end, "scope": scope, "max_chars": max_chars}, ensure_ascii=False)
    remote_cmd = "python3 -c " + shlex.quote(REMOTE_CONTENT_CODE) + " " + shlex.quote(payload)
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}", alias, remote_cmd]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=max(20, timeout + 20))
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip())
    data = json.loads(proc.stdout.strip().splitlines()[-1])
    return data.get("messages") or []


def annotate_deep_link(item: Dict[str, Any]) -> None:
    tid = item.get("thread_id") or ""
    item["deep_link"] = f"codex://thread/{tid}" if tid else ""
    item["deep_link_status"] = "best_effort"


def choose_best(candidates: Iterable[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    ranked = rank_candidates(candidates)
    return ranked[0] if ranked else None


def rank_candidates(candidates: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pool = list(candidates)
    if not pool:
        return []
    return sorted(
        pool,
        key=lambda c: (
            int(c.get("user_count") or 0),
            int(c.get("event_count") or 0),
            float(c.get("last_user_ts") or 0),
            str(c.get("thread_id") or ""),
        ),
        reverse=True,
    )


def render_conversation_markdown(candidate: Dict[str, Any], messages: List[Dict[str, Any]]) -> str:
    lines = [
        f"# Codex Conversation Export",
        "",
        f"- Thread ID: {candidate.get('thread_id', '')}",
        f"- Source: {candidate.get('source', '')}" + (f" ({candidate.get('remote_alias')})" if candidate.get("remote_alias") else ""),
        f"- Title: {candidate.get('title') or '<unknown>'}",
        f"- Working directory: {candidate.get('cwd') or candidate.get('remote_path') or '<unknown>'}",
        f"- Rollout path: {candidate.get('rollout_path') or '<unknown>'}",
        f"- Exported messages: {len(messages)}",
        "",
    ]
    for index, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        timestamp = msg.get("timestamp") or ""
        lines.append(f"## {index}. {role} {timestamp}".rstrip())
        lines.append("")
        lines.append(msg.get("text") or "")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def extract_candidate_content(candidate: Dict[str, Any], args: argparse.Namespace, start: float, end: float) -> List[Dict[str, Any]]:
    rollout_path = candidate.get("rollout_path")
    if not rollout_path:
        raise RuntimeError("no session JSONL path is available")
    if candidate.get("source") == "remote-ssh":
        alias = candidate.get("remote_alias")
        if not alias:
            raise RuntimeError("missing remote SSH alias for selected thread")
        return extract_remote_content(alias, rollout_path, args.ssh_timeout, start, end, args.content_scope, args.max_message_chars)
    return extract_local_content(Path(rollout_path), start, end, args.content_scope, args.max_message_chars)


def candidate_export_name(index: int, candidate: Dict[str, Any]) -> str:
    thread_id = candidate.get("thread_id") or "unknown-thread"
    return f"{index:02d}-{thread_id}.md"


def attach_content(result: Dict[str, Any], args: argparse.Namespace, start: float, end: float) -> None:
    selected = result.get("top_candidates") or ([result["best"]] if result.get("best") else [])
    if not selected:
        return

    output_dir = Path(args.content_output_dir).expanduser() if args.content_output_dir else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    for index, candidate in enumerate(selected, 1):
        try:
            messages = extract_candidate_content(candidate, args, start, end)
        except Exception as exc:
            candidate["conversation"] = {"scope": args.content_scope, "error": str(exc)}
            result.setdefault("warnings", []).append(f"Conversation content export failed for {candidate.get('thread_id')}: {exc}")
            continue

        conversation = {"scope": args.content_scope, "message_count": len(messages)}
        if output_dir:
            output = output_dir / candidate_export_name(index, candidate)
            output.write_text(render_conversation_markdown(candidate, messages), encoding="utf-8")
            conversation["output_path"] = str(output)
        elif index == 1 and args.content_output:
            output = Path(args.content_output).expanduser()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_conversation_markdown(candidate, messages), encoding="utf-8")
            conversation["output_path"] = str(output)
        else:
            conversation["messages"] = messages
        candidate["conversation"] = conversation

    best = result.get("best")
    if best:
        match = next((c for c in selected if c.get("thread_id") == best.get("thread_id")), None)
        if match and match.get("conversation"):
            result["conversation"] = match["conversation"]


def human_report(result: Dict[str, Any]) -> str:
    lines = []
    best = result.get("best")
    if not best:
        lines.append("No Codex thread with user messages was found in the requested time range.")
    else:
        top_candidates = result.get("top_candidates") or [best]
        heading = "Most active thread:" if len(top_candidates) == 1 else f"Top {len(top_candidates)} active threads:"
        lines.append(heading)
        for rank, item in enumerate(top_candidates, 1):
            title = item.get("title") or "<unknown>"
            if len(title) > 180:
                title = title[:177] + "..."
            prefix = "" if len(top_candidates) == 1 else f"{rank}. "
            lines.append(f"{prefix}- Source: {item.get('source')}" + (f" ({item.get('remote_alias')})" if item.get("remote_alias") else ""))
            lines.append(f"{prefix}- Title: {title}")
            lines.append(f"{prefix}- Thread ID: {item.get('thread_id')}")
            lines.append(f"{prefix}- Deep link: {item.get('deep_link')} ({item.get('deep_link_status')})")
            lines.append(f"{prefix}- Working directory: {item.get('cwd') or item.get('remote_path') or '<unknown>'}")
            lines.append(f"{prefix}- User messages in range: {item.get('user_count')}")
            lines.append(f"{prefix}- Evidence: {item.get('evidence')}" + (f", rollout: {item.get('rollout_path')}" if item.get("rollout_path") else ""))
            if item.get("last_user_ts"):
                lines.append(f"{prefix}- Last user message: {iso(item.get('last_user_ts'))}")
            conversation = item.get("conversation")
            if conversation:
                if conversation.get("output_path"):
                    lines.append(f"{prefix}- Conversation content: saved to {conversation.get('output_path')}")
                elif conversation.get("error"):
                    lines.append(f"{prefix}- Conversation content: export failed: {conversation.get('error')}")
                else:
                    lines.append(f"{prefix}- Conversation content: {conversation.get('message_count', 0)} messages included below")
    diags = result.get("remote_diagnostics") or []
    if not diags:
        if result.get("remote_connection_count"):
            lines.append("Remote SSH diagnostics: configured Remote SSH connections found; remote probing was skipped.")
        else:
            lines.append("Remote SSH diagnostics: no configured Remote SSH connections found in local Codex state.")
    else:
        lines.append("Remote SSH diagnostics:")
        for d in diags:
            if d.get("ok"):
                lines.append(f"- {d.get('alias')}: ok; homes={len(d.get('homes') or [])}; candidates={len(d.get('candidates') or [])}")
            else:
                lines.append(f"- {d.get('alias')}: failed; {d.get('error')}")
    if result.get("warnings"):
        lines.append("Warnings:")
        for warning in result["warnings"]:
            lines.append(f"- {warning}")
    conversation = result.get("conversation")
    if conversation and not conversation.get("output_path"):
        lines.append("")
        lines.append(render_conversation_markdown(best, conversation.get("messages") or []))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Find the most active Codex thread in a time range.")
    parser.add_argument("--start", required=True, help="Start time, e.g. 2026-06-15 or 2026-06-15 00:00")
    parser.add_argument("--end", required=True, help="End time, e.g. 2026-06-15 or 2026-06-15 23:59:59")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"))
    parser.add_argument("--limit", type=int, default=1, help="Number of ranked threads to return.")
    parser.add_argument("--ssh-timeout", type=int, default=5)
    parser.add_argument("--no-remote", action="store_true", help="Skip Remote SSH probing.")
    parser.add_argument("--include-content", action="store_true", help="Include the selected thread's user/assistant conversation content.")
    parser.add_argument("--content-output", help="Save selected thread conversation content to this Markdown file.")
    parser.add_argument("--content-output-dir", help="Save each selected top thread conversation to a Markdown file in this directory.")
    parser.add_argument("--content-scope", choices=["range", "full"], default="range", help="Export only messages in the time range or the full selected thread.")
    parser.add_argument("--max-message-chars", type=int, default=4000, help="Truncate each exported message to this many characters; use 0 for no per-message truncation.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    args = parser.parse_args()

    tz = local_tz(args.timezone)
    start = parse_time(args.start, is_end=False, tz=tz)
    end = parse_time(args.end, is_end=True, tz=tz)
    if start > end:
        raise SystemExit("--start must be before --end")
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    home = Path(args.codex_home).expanduser()
    state = load_global_state(home)
    connections, projects, assignments = remote_maps(state)

    local_candidates, local_errors = scan_local(home, start, end)
    prompt_candidates = prompt_history_candidates(state, connections, projects, assignments)

    remote_diagnostics = []
    remote_candidates = []
    if not args.no_remote:
        for host_id, conn in connections.items():
            alias = conn.get("alias") or conn.get("displayName")
            if not alias:
                remote_diagnostics.append({"host_id": host_id, "ok": False, "error": "missing SSH alias", "candidates": []})
                continue
            diag = scan_remote(alias, host_id or "", args.ssh_timeout, start, end)
            remote_diagnostics.append(diag)
            remote_candidates.extend(diag.get("candidates") or [])

    all_candidates = local_candidates + remote_candidates
    precise_ids = {c.get("thread_id") for c in all_candidates}
    fallback_candidates = [c for c in prompt_candidates if c.get("thread_id") not in precise_ids]
    all_candidates += fallback_candidates
    for item in all_candidates:
        annotate_deep_link(item)

    ranked_candidates = rank_candidates(all_candidates)
    top_candidates = ranked_candidates[: args.limit]
    best = top_candidates[0] if top_candidates else None
    warnings = []
    if connections and not remote_diagnostics:
        warnings.append("Remote SSH connections exist but remote probing was skipped.")
    if remote_diagnostics and any(not d.get("ok") for d in remote_diagnostics):
        warnings.append("Remote SSH coverage is incomplete because at least one alias failed.")
    if any(c.get("evidence") == "prompt_history_no_timestamps" for c in top_candidates):
        warnings.append("At least one selected candidate is based on prompt-history without per-message timestamps; session JSONL verification or content export may be missing.")
    if local_errors:
        warnings.append(f"Local session scan had {len(local_errors)} unreadable rollout files.")

    result = {
        "range": {"start": iso(start), "end": iso(end), "timezone": args.timezone},
        "best": best,
        "top_candidates": top_candidates,
        "candidate_count": len(all_candidates),
        "remote_connection_count": len(connections),
        "remote_diagnostics": remote_diagnostics,
        "warnings": warnings,
        "local_errors_sample": local_errors[:20],
    }
    if args.include_content or args.content_output or args.content_output_dir:
        attach_content(result, args, start, end)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(human_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
