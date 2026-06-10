#!/usr/bin/env python3
"""Build a reward/state skeleton for one testcase RL rollout.

This script intentionally handles only deterministic parsing. It does not infer
the human root cause; the skill user must read the raw TXT and fill that part.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


COMPILE_SUCCESS_TOKEN = "OVERALL TEST SUMMARY"
COMPILE_FAILURE_TOKEN = "terminated with exit code [1]"
TESTED_RE = re.compile(r"TESTED:\s*(\d+)")
PASSED_RE = re.compile(r"PASSED:\s*(\d+)")
FAILED_RE = re.compile(r"FAILED:\s*(\d+)")
COVERAGE_RE = re.compile(r"覆盖率:\s*(\d+(?:\.\d+)?)%")
TOTAL_REWARD_RE = re.compile(r"总奖励:\s*([-+]?\d+(?:\.\d+)?)")
REWARD_DETAIL_RE = re.compile(
    r"compile=(?P<compile>True|False)\s+coverage=(?P<coverage>N/A|[-+]?\d+(?:\.\d+)?%?)\s+"
    r"base=(?P<base>[-+]?\d+(?:\.\d+)?)\s+exception=(?P<exception>True|False)"
)
TERMINATION_RE = re.compile(r"TerminationReason\.([A-Z_]+)|termination_reason['\"]?\s*[:=]\s*['\"]?([A-Z_]+)")
STEP_RE = re.compile(r"Step\s+(\d+)")


def load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    with path.open(encoding="utf-8", errors="replace") as f:
        return json.load(f)


def read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def find_one(paths: list[Path]) -> Path | None:
    return paths[0] if paths else None


def resolve_paths(input_path: Path | None, json_path: Path | None, txt_path: Path | None) -> tuple[Path | None, Path | None, Path | None]:
    token_stats_path: Path | None = None

    if input_path is not None:
        if input_path.is_dir():
            json_path = json_path or find_one(sorted(input_path.glob("*.json")))
            txt_path = txt_path or find_one(sorted(input_path.glob("*.txt")))
            token_stats_path = find_one(sorted(input_path.glob("*token*stats*.json")))
        elif input_path.suffix == ".json":
            json_path = json_path or input_path
        elif input_path.suffix in {".txt", ".log"}:
            txt_path = txt_path or input_path

    if json_path is not None and txt_path is None:
        candidate = json_path.with_suffix(".txt")
        if candidate.exists():
            txt_path = candidate
    if txt_path is not None and json_path is None:
        candidate = txt_path.with_suffix(".json")
        if candidate.exists():
            json_path = candidate

    base = json_path or txt_path
    if token_stats_path is None and base is not None:
        for candidate in sorted(base.parent.glob("*token*stats*.json")):
            token_stats_path = candidate
            break

    return json_path, txt_path, token_stats_path


def parse_task(data: dict[str, Any] | None) -> dict[str, Any]:
    task = (data or {}).get("task") or {}
    trajs = (data or {}).get("trajectories") or []
    traj = trajs[0] if trajs else {}
    uid = traj.get("uid")
    rollout_id = None
    if isinstance(uid, str) and ":" in uid:
        rollout_id = f"rollout_{uid.rsplit(':', 1)[-1]}"
    return {
        "data_uid": task.get("data_uid"),
        "repo_name": task.get("repo_name"),
        "function_name": task.get("function_name"),
        "rollout_id": rollout_id,
        "original_reward": traj.get("reward", (data or {}).get("reward")),
        "termination_reason": (data or {}).get("termination_reason"),
    }


def parse_test_stats(text: str) -> tuple[int | None, int | None, int | None]:
    tested_matches = TESTED_RE.findall(text)
    passed_matches = PASSED_RE.findall(text)
    failed_matches = FAILED_RE.findall(text)
    tested = int(tested_matches[-1]) if tested_matches else None
    passed = int(passed_matches[-1]) if passed_matches else None
    failed = int(failed_matches[-1]) if failed_matches else None
    return tested, passed, failed


def parse_last_coverage(text: str) -> float | None:
    matches = COVERAGE_RE.findall(text)
    return float(matches[-1]) if matches else None


def parse_reward_log(text: str) -> dict[str, Any]:
    reward_matches = TOTAL_REWARD_RE.findall(text)
    detail_matches = list(REWARD_DETAIL_RE.finditer(text))
    detail = detail_matches[-1] if detail_matches else None

    total_reward = float(reward_matches[-1]) if reward_matches else None
    if detail is None:
        return {"txt_reward": total_reward}

    cov_raw = detail.group("coverage")
    coverage = None if cov_raw == "N/A" else float(cov_raw.rstrip("%"))
    return {
        "txt_reward": total_reward,
        "compile_success": detail.group("compile") == "True",
        "coverage": coverage,
        "base_reward": float(detail.group("base")),
        "is_exception_trajectory": detail.group("exception") == "True",
    }


def compute_base_reward(compile_success: bool, all_tests_pass: bool, pass_rate: float, coverage: float | None) -> float:
    if not compile_success:
        return 0.0
    if not all_tests_pass:
        return round(0.3 * pass_rate, 4)
    if coverage is None:
        return 0.3
    return round(0.3 + 0.7 * min(coverage / 90.0, 1.0), 4)


def infer_exception(text: str, termination_reason: str | None, reward_log: dict[str, Any]) -> tuple[bool, str | None]:
    reason = termination_reason
    for match in TERMINATION_RE.finditer(text):
        reason = match.group(1) or match.group(2) or reason
    exception = bool(reward_log.get("is_exception_trajectory"))
    exception = exception or any(token in text for token in ["MAX_PROMPT_LENGTH_EXCEEDED", "MAX_TURNS_EXCEEDED", "TIMEOUT", "Terminated:"])
    return exception, reason


def safe_close(a: Any, b: Any) -> bool | None:
    if a is None or b is None:
        return None
    try:
        return math.isclose(float(a), float(b), abs_tol=1e-4)
    except Exception:
        return False


def build_skeleton(json_path: Path | None, txt_path: Path | None, token_stats_path: Path | None) -> dict[str, Any]:
    data = load_json(json_path)
    text = read_text(txt_path)
    task_info = parse_task(data)
    reward_log = parse_reward_log(text)

    compile_success_count = text.count(COMPILE_SUCCESS_TOKEN)
    compile_error_count = text.count(COMPILE_FAILURE_TOKEN)
    if compile_error_count == 0:
        compile_error_count = len(re.findall(r"(?i)(error:|undefined reference|too few arguments|too many arguments)", text))

    compile_success = bool(reward_log.get("compile_success")) if "compile_success" in reward_log else compile_success_count > 0
    tested, passed, failed = parse_test_stats(text)
    if failed is not None:
        all_tests_pass = failed == 0
        pass_rate = (passed / tested) if tested and passed is not None else (1.0 if all_tests_pass else 0.0)
    else:
        base_from_log = reward_log.get("base_reward")
        if compile_success and base_from_log is not None and base_from_log < 0.3:
            all_tests_pass = False
            pass_rate = round(float(base_from_log) / 0.3, 4)
        else:
            all_tests_pass = bool(compile_success)
            pass_rate = 1.0 if all_tests_pass else 0.0

    coverage = reward_log.get("coverage")
    if coverage is None:
        coverage = parse_last_coverage(text)
    is_exception, termination_reason = infer_exception(text, task_info.get("termination_reason"), reward_log)

    base_reward = compute_base_reward(compile_success, all_tests_pass, pass_rate, coverage)
    final_reward = round(base_reward * 0.6, 4) if is_exception else base_reward
    original_reward = task_info.get("original_reward")
    if original_reward is None:
        original_reward = reward_log.get("txt_reward")

    calc = (
        f"final_reward = round(base_reward * exception_penalty_factor, 4) = "
        f"round({base_reward} * 0.6, 4) = {final_reward}"
        if is_exception
        else f"final_reward = base_reward = {base_reward}"
    )

    if not compile_success:
        plain = "最终编译失败，因此 base_reward=0，final_reward=0。"
    elif not all_tests_pass:
        plain = f"最终编译成功但测试未全过，因此 base_reward=0.3*pass_rate=0.3*{pass_rate}={base_reward}。"
    elif coverage is None:
        plain = "最终编译成功且测试全过，但没有覆盖率，因此 base_reward=0.3。"
    else:
        plain = f"最终编译成功且测试全过，coverage={coverage}，因此 base_reward=0.3+0.7*min({coverage}/90,1)={base_reward}。"
    if is_exception:
        plain += " 轨迹属于异常退出，因此乘以 exception_penalty_factor=0.6。"

    max_step = None
    step_matches = STEP_RE.findall(text)
    if step_matches:
        max_step = max(int(x) for x in step_matches)

    return {
        "data_uid": task_info.get("data_uid"),
        "repo_name": task_info.get("repo_name"),
        "function_name": task_info.get("function_name"),
        "rollout_id": task_info.get("rollout_id"),
        "original_reward": original_reward,
        "recomputed_reward": final_reward,
        "reward_match": safe_close(original_reward, final_reward),
        "final_compile_success": compile_success,
        "all_tests_pass": all_tests_pass,
        "intermediate_compile_error_count": compile_error_count,
        "compile_success_count": compile_success_count,
        "length_limit_or_context_exceeded": any(token in text for token in ["MAX_PROMPT_LENGTH_EXCEEDED", "ContextWindowExceeded", "context length"]),
        "termination_reason": termination_reason,
        "reward_explanation": {
            "formula_version": "testcase_reward_fn_v2",
            "parse_source": "txt_reward_log" if reward_log else "json_or_txt_scan",
            "compile_success": compile_success,
            "all_tests_pass": all_tests_pass,
            "tested": tested,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(pass_rate, 4),
            "coverage": coverage,
            "base_reward": base_reward,
            "is_exception_trajectory": is_exception,
            "exception_penalty_factor": 0.6 if is_exception else None,
            "final_reward": final_reward,
            "calculation": calc,
            "plain_explanation": plain,
        },
        "root_cause_analysis": {
            "type": "",
            "summary": "",
            "reason": "",
            "not_terminal_reason": "",
        },
        "first_failure_location": {
            "phase": "",
            "step": "",
            "explanation": "",
        },
        "final_failure_reason": "length_limit_exceeded" if is_exception and (termination_reason or "").endswith("EXCEEDED") else "",
        "key_evidence": [],
        "failure_chain": [],
        "sft_fix_direction_candidate": "",
        "json_path": str(json_path) if json_path else None,
        "txt_path": str(txt_path) if txt_path else None,
        "token_stats_path": str(token_stats_path) if token_stats_path else None,
        "max_step_seen": max_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze one testcase rollout reward skeleton.")
    parser.add_argument("path", nargs="?", help="Rollout directory, .json trace, or .txt log.")
    parser.add_argument("--json", dest="json_path", help="Explicit JSON trace path.")
    parser.add_argument("--txt", dest="txt_path", help="Explicit TXT log path.")
    parser.add_argument("--output", help="Output JSON path. If omitted, print to stdout only.")
    args = parser.parse_args()

    input_path = Path(args.path).expanduser().resolve() if args.path else None
    json_path = Path(args.json_path).expanduser().resolve() if args.json_path else None
    txt_path = Path(args.txt_path).expanduser().resolve() if args.txt_path else None
    out_path = Path(args.output).expanduser().resolve() if args.output else None

    json_path, txt_path, token_stats_path = resolve_paths(input_path, json_path, txt_path)
    result = build_skeleton(json_path, txt_path, token_stats_path)
    text = json.dumps(result, ensure_ascii=False, indent=2)

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
