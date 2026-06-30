#!/usr/bin/env python3
"""Extract compact step inventories from testcase agent log/json traces."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


STEP_RE = re.compile(
    r"^.*?Step\s+(\d+).*?$",
    re.MULTILINE,
)


def compact_text(value: Any, limit: int = 500) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def extract_uid(path: Path, data: dict[str, Any] | None = None) -> str | None:
    if data:
        uid = data.get("data_uid") or data.get("uid") or data.get("case_id")
        if uid:
            return str(uid)
    match = re.search(r"data_uid_([A-Za-z0-9_-]+)", path.name)
    if match:
        return match.group(1).removesuffix(".log").removesuffix(".json")
    return None


def summarize_step(step: dict[str, Any]) -> dict[str, Any]:
    blob = "\n".join(
        compact_text(step.get(key), 2000)
        for key in (
            "model_output",
            "model_output_message",
            "code_action",
            "tool_calls",
            "observations",
            "action_output",
            "error",
        )
    )
    tool_calls = compact_text(step.get("tool_calls") or step.get("code_action"), 600)
    error = compact_text(step.get("error"), 600)
    observations = compact_text(step.get("observations") or step.get("action_output"), 800)
    tags = []
    tag_patterns = {
        "compile": r"compile_ceedling_repo|ceedling",
        "coverage": r"get_coverage_report|覆盖率|coverage",
        "create_file": r"create_new_file|Created file|Overwritten file",
        "filename_error": r"filename_convention|文件名不符合",
        "context_limit": r"ContextWindowExceeded|max token|maximum context",
        "final": r"final_answer|is_final_answer",
        "mock_error": r"mock_correct|内部函数.*mock|mock.*内部",
        "parse_error": r"Code parsing failed|SyntaxError",
    }
    for tag, pattern in tag_patterns.items():
        if re.search(pattern, blob, re.IGNORECASE):
            tags.append(tag)
    return {
        "step_number": step.get("step_number"),
        "tags": tags,
        "tool_calls": tool_calls,
        "error": error,
        "observations": observations,
    }


def parse_json_trace(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    steps = data.get("steps") if isinstance(data, dict) else None
    if not isinstance(steps, list):
        steps = []
    return {
        "path": str(path),
        "format": "json",
        "uid": extract_uid(path, data if isinstance(data, dict) else None),
        "total_steps": len(steps),
        "steps": [summarize_step(step) for step in steps if isinstance(step, dict)],
    }


def parse_log_trace(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = list(STEP_RE.finditer(text))
    steps = []
    if matches:
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            chunk = text[start:end]
            pseudo = {
                "step_number": match.group(1),
                "model_output": chunk,
                "observations": chunk,
                "error": "",
            }
            steps.append(summarize_step(pseudo))
    else:
        pseudo = {
            "step_number": None,
            "model_output": text,
            "observations": text,
            "error": "",
        }
        steps.append(summarize_step(pseudo))
    return {
        "path": str(path),
        "format": "log",
        "uid": extract_uid(path),
        "total_steps": len(steps),
        "steps": steps,
    }


def parse_trace(path_str: str) -> dict[str, Any]:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        return parse_json_trace(path)
    return parse_log_trace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, help="Baseline trajectory log/txt/json path")
    parser.add_argument("--experiment", required=True, help="Experiment trajectory log/txt/json path")
    args = parser.parse_args()
    result = {
        "baseline": parse_trace(args.baseline),
        "experiment": parse_trace(args.experiment),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
