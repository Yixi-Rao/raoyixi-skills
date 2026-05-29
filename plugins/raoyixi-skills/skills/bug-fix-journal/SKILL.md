---
name: bug-fix-journal
description: 在代码仓库改动、适配、优化、迁移、调试、测试失败修复、依赖升级、API 兼容性调整等任务中，遇到并修复具体 bug/error 时，将 bug 详情、证据、分析、探索过程、失败尝试、最终方案、验证结果和后续事项记录为结构化中文 Markdown 文件。Use when a fix should leave a reusable Chinese written trace for future debugging and maintenance.
---

# Bug Fix Journal

## 目标

当仓库工作中发现并修复具体 bug/error 时，使用本 skill 留下一份中文 Markdown 记录。记录应让未来的维护者或 agent 不必重新翻日志、猜上下文，就能理解故障现象、调查路径、根因和解决方案。

## 记录位置

默认在仓库内统一创建并维护这个目录：

```text
docs/bug-fix-journal/
```

如果仓库已有明显的 bug 记录目录，例如 `docs/bugs/`、`docs/debug/`、`debug-notes/`，或者用户指定了目录，则沿用该目录。一个仓库内尽量只使用一个统一目录。

文件名使用 bug 名称的英文/拼音/技术关键词，统一转为小写 hyphen-case：

```text
docs/bug-fix-journal/<bug-name>.md
```

示例：

```text
docs/bug-fix-journal/qwen35-sft-loss-mask-zero.md
docs/bug-fix-journal/hydra-missing-sft-trainer-config.md
docs/bug-fix-journal/api-timeout-on-empty-response.md
```

## 何时记录

同时满足以下条件时，创建或更新记录：

- 存在明确 bug/error、失败测试、traceback、异常行为、迁移兼容性问题或运行时问题。
- 你进行了有针对性的分析、排查或代码/配置修复。
- 这些信息未来对维护、回归分析、迁移适配或类似问题修复有复用价值。

纯样式调整、没有调查过程的一行 typo 修复、没有形成 bug 诊断的临时探索，不需要创建记录。

## 工作流

1. 从现象或根因中提炼一个短 bug 名。
2. 创建统一记录目录。
3. 创建或更新对应 bug 的 Markdown 文件。
4. 调查过程中持续记录事实，不要只在最后补一段总结。
5. 记录必须绑定证据：命令、错误、文件路径、配置键、测试名、日志片段、观察到的行为。
6. 修复后补充最终方案和验证结果。

可使用内置脚本生成中文模板：

```bash
python <skill-dir>/scripts/create_bug_record.py \
  --repo /path/to/repo \
  --bug "Hydra missing sft trainer config" \
  --summary "agent_sft_trainer.yaml 引用了当前 verl checkout 中不存在的配置名"
```

脚本会创建 `docs/bug-fix-journal/<bug-name>.md`。默认不会覆盖已有记录，除非传入 `--force`。

## 记录模板

每份记录应包含以下中文章节。内容保持简洁，但要具体。

````markdown
# <Bug 名称>

## 状态

- 状态：调查中 | 已修复 | 已缓解 | 暂缓
- 首次发现：<日期或上下文>
- 仓库/分支：<仓库路径和分支>

## 摘要

<用一段话说明 bug 是什么、影响是什么。>

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
````

## 质量要求

- 使用中文记录正文，保留英文错误原文、命令名、文件名、配置键和代码符号。
- 写清楚具体文件路径和命令。
- 长日志只摘录最小有用片段。
- 明确区分观察到的证据和自己的推断。
- 如果修复不完整，写清楚剩余问题和恢复调查的方法。
- bug 复发时更新同一个记录，不要创建多个近似重复文件。

## 修复过程中

调查尚未完成时，也可以先创建 `状态：调查中` 的部分记录。后续再补根因、修复方案和验证结果。准确的半成品记录比丢失调查过程更有价值。
