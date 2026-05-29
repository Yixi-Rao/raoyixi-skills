#!/usr/bin/env python3
"""Create a structured Chinese bug-fix journal Markdown file."""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime
from pathlib import Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "bug-record"


def git_value(repo: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "unknown"


def build_content(repo: Path, bug: str, summary: str, state: str) -> str:
    branch = git_value(repo, ["branch", "--show-current"])
    commit = git_value(repo, ["rev-parse", "--short", "HEAD"])
    today = datetime.now().strftime("%Y-%m-%d")
    state_labels = {
        "investigating": "调查中",
        "fixed": "已修复",
        "mitigated": "已缓解",
        "deferred": "暂缓",
    }
    summary_text = summary or "<用一段话说明 bug 是什么、影响是什么。>"
    state_text = state_labels.get(state, state)

    return f"""# {bug}

## 状态

- 状态：{state_text}
- 首次发现：{today}
- 仓库/分支：{repo} @ {branch} ({commit})

## 摘要

{summary_text}

## 现象

- <观察到的错误、失败测试、异常命令、用户可见行为>

## 证据

```text
<关键 traceback、命令输出、日志片段或复现信号>
```

## 根因分析

<说明 bug 的根因。区分事实、推断和已排除的可能性。>

## 排查过程

- <检查了什么、尝试了什么、对比了什么、排除了什么>
- <失败尝试也要记录，只要它改变了诊断方向>

## 修复方案

- 修改文件：
  - `<path>`
- 方案说明：
  <改了什么，为什么这是合适的修复。>

## 验证结果

- <执行的命令/测试/检查>
- <结果>

## 后续事项

- <回归测试、清理、文档、风险或后续工作>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Chinese bug-fix journal Markdown file.")
    parser.add_argument("--repo", default=".", help="Repository root where the journal folder should be created.")
    parser.add_argument("--bug", required=True, help="Human-readable bug name. Used for title and filename.")
    parser.add_argument("--summary", default="", help="Optional Chinese one-paragraph summary.")
    parser.add_argument("--folder", default="docs/bug-fix-journal", help="Journal folder relative to repo.")
    parser.add_argument("--state", default="investigating", choices=["investigating", "fixed", "mitigated", "deferred"])
    parser.add_argument("--force", action="store_true", help="Overwrite an existing record.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    output_dir = repo / args.folder
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{slugify(args.bug)}.md"
    if output_file.exists() and not args.force:
        print(output_file)
        return 0

    output_file.write_text(build_content(repo, args.bug.strip(), args.summary.strip(), args.state), encoding="utf-8")
    print(output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
