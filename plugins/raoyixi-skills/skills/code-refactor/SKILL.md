---
name: code-refactor
description: Use when the user requests codebase automation tasks through a "需求" command, including autocommit, autofix, autosummary, autodoc, autointerpret, or auto-merge-request for GitLab issue/MR workflows. Use auto-merge-request when asked to push a branch, create a review-ready GitLab MR, create/link an issue, or ensure merge closes the issue.
---

# code-refactor Skill

## Overview

Triggered when the user requests an automated code refactoring operation. You must request the user to provide a `需求` parameter specifying which operation to perform.

## Required Input

The user **must** specify a `需求` parameter with one of the following values:

| 需求 | 功能 | 对应文件 |
|---|---|---|
| `autocommit` | 自动化代码分析与提交流程 | `commands/autocommit.md` |
| `autofix` | Pre-commit 代码扫描自动修复 | `commands/autofix.md` |
| `autosummary` | 自动化代码摘要/变更总结 | `commands/autosummary.md` |
| `autodoc` | 自动化文档生成 | `commands/autodoc.md` |
| `autointerpret` | 自动化代码解释 | `commands/autointerpret.md` |
| `auto-merge-request` | GitLab Issue/MR 创建、关联和 review-ready 校验 | `commands/auto-merge-request.md` |

## Execution Logic

1. Parse the user's `需求` parameter from the task description.
2. Load the corresponding markdown file from `commands/<需求>.md`.
3. Execute the procedures described in that markdown file step by step against the target codebase.
4. If `需求` is missing or invalid, ask the user to specify it explicitly.

## Workflow

1. **Identify target directory**: Determine the workspace / repository the user wants to operate on.
2. **Load command**: Read the appropriate `commands/<需求>.md` file.
3. **Execute**: Follow the markdown's instructions precisely — run the specified git commands, generate changelogs, apply fixes, etc.
4. **Output**: Present the results (commit, diff, changelog, generated docs, etc.) to the user.

## Notes

- The `clean.md` file (`commands/clean.md`) is a supplementary guide for large file cleanup, referenced by `autocommit.md` when large files block git push.
- `auto-merge-request` owns GitLab MR lifecycle automation and may use `scripts/gitlab_auto_mr.py`.
- Always confirm the target repository exists and is a git repository before starting.
- Use the repository's existing patterns and tools (ruff, pre-commit, etc.) as described in each command file.
