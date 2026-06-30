---
name: testcase-trace-compare-analysis
description: Compare two testcase-generation agent trajectories step by step, usually baseline vs SFT/experiment logs or JSON traces. Use when the user asks to read two log/txt/json trajectories, decompose by Step blocks or SOP phases, explain baseline and experiment behavior at every step, identify experiment anomalies/advantages/crashes, repetition loops, and write a Markdown report under /lpai/测试用例 SFT 轨迹对比分析.
---

# Testcase Trace Compare Analysis

Use this skill to produce a detailed Chinese Markdown analysis comparing two testcase-generation agent trajectories.

## Required Inputs

Before analysis, ensure the user provided both:

- A baseline trajectory file path or attachment.
- An experiment trajectory file path or attachment.

Also ensure the user explicitly identifies which trajectory is baseline and which is experiment. If either file or role mapping is missing, stop and ask for it.

Accepted inputs:

- `.log` / `.txt` files with blocks like `━━━━━━━━ Step ? ━━━━━━━━`.
- `.json` files containing `steps`, `messages`, `data_uid`, or similar trace fields.

Do not modify source code, git state, evaluation outputs, or the trajectories. Reading files and writing the requested Markdown report is allowed.

## Output Location

Write the final report to:

```text
/lpai/测试用例 SFT 轨迹对比分析/<uid>.md
```

Use the `data_uid` from JSON if present. Otherwise infer the uid from filenames such as `data_uid_<uid>.log`. If no uid is available, use a short deterministic name derived from both filenames, for example `baseline_vs_experiment.md`.

Create the output directory if needed.

## Workflow

1. Read both trajectory files completely.
   - You must inspect the full content, not only grep hits or tail excerpts.
   - For long traces, use scripts/tools to extract structure, then return to the raw file around key failure points.
   - Preserve exact file paths and line references when citing evidence.

2. Parse both trajectories into steps.
   - For log/txt files, split by `━━━━━━━━ Step <n> ━━━━━━━━`.
   - For JSON files, use the `steps` array when present.
   - Extract for each step: step number, thought/intent, code/tool call, observations, errors, final answer flag, token/context errors, and file paths touched.

3. Group steps by SOP phase, not only by raw step number.
   Use these default phases when applicable:
   - `task_and_constraints`: task prompt, SOP, success criteria.
   - `function_analysis`: read target function body.
   - `support_analysis`: read `test/support` and dependency files.
   - `mock_analysis`: inspect CMock/mock functions.
   - `conditional_macro_analysis`: inspect conditional compilation combinations.
   - `test_generation`: create or edit test file.
   - `compile_validation`: call `compile_ceedling_repo`.
   - `coverage_validation`: call `get_coverage_report`.
   - `repair_loop`: repeated fix/retry after tool feedback.
   - `finalization`: final answer, final coverage, or terminal failure.

4. Compare each SOP phase in order.
   For every phase, write:
   - Phase description: what this phase should accomplish.
   - Baseline behavior: what baseline did, with evidence.
   - Experiment behavior: what experiment did, with evidence.
   - Delta: experiment anomaly, advantage, crash, missing step, or same behavior.
   - Cause: why the behavior matters and how it affects compile/coverage/final outcome.

5. Handle repetition explicitly.
   - If one trajectory has no corresponding step because the other entered a loop, switch to single-trajectory analysis for the loop.
   - Count repeated actions and repeated error messages when possible.
   - Explain why the loop repeats: wrong hypothesis, wrong path, ignored tool feedback, invalid tool argument, context growth, or another cause.

6. Identify the first real divergence.
   - Do not treat the final error as the root cause if an earlier behavior caused it.
   - Distinguish downstream symptoms such as `ContextWindowExceeded`, max token, or no coverage from the first wrong action.

7. Write a mandatory core conclusion / root cause statement.
   - Put it near the top of the report, before detailed phase analysis.
   - State the root cause in one to three concrete paragraphs, not only as bullet fragments.
   - Use the pattern: "This case failed not because of <misleading final symptom or weak hypothesis>, but because <first wrong behavior/root cause>."
   - Include the most important baseline-vs-experiment contrast, such as different tool arguments, different file path handling, different mock strategy, or different repair hypothesis.
   - Explicitly connect the root cause to downstream symptoms: compile failure, coverage drop, repeated loop, context overflow, missing final answer, or crash.
   - Keep it evidence-backed and actionable; avoid vague claims like "model capability is weak" unless the trace proves a specific behavior.

8. Produce a final report in Chinese.
   Keep claims evidence-backed. Use concise quotes or paraphrases from logs; avoid huge pasted trace blocks.

## Optional Helper Script

Use `scripts/extract_trace_steps.py` to create a compact inventory:

```bash
python /lpai/.codex-llm-eval-home/skills/testcase-trace-compare-analysis/scripts/extract_trace_steps.py \
  --baseline /abs/path/baseline.log \
  --experiment /abs/path/experiment.log
```

The script only reads files and prints JSON. It does not replace full reading; use it to locate steps and repeated patterns quickly.

## Report Template

Use this structure unless the user requests a different one:

```markdown
# 测试用例生成轨迹对比分析：<uid>

## 1. 输入轨迹

- baseline: `<abs path>`
- experiment: `<abs path>`
- uid: `<uid>`

## 2. 结论摘要

核心结论：

这个 case 的失败根因不是 `<表面现象或不充分解释>`，而是 `<第一处可证据化的错误行为>`。Baseline 在 `<关键动作>` 上使用了 `<正确模式>`，而 experiment/SFT 使用了 `<错误模式>`，导致 `<直接错误>`，随后 `<循环/放大机制>`，最终 `<终局失败，如 context 超限、coverage=0、compile failed>`。

- 第一分歧点：
- 实验轨迹主异常：
- 是否属于 compile regression：
- 是否属于 coverage regression：
- 直接失败原因：
- 上游根因：

## 3. 总览指标

| 指标 | baseline | experiment | 结论 |
| --- | ---: | ---: | --- |
| 总 step 数 | | | |
| 是否 final_answer | | | |
| 编译是否通过 | | | |
| 覆盖率 | | | |
| 重复/循环次数 | | | |
| 终止原因 | | | |

## 4. SOP 阶段逐步对照

### 4.x <phase name>

步骤目标：

baseline 行为：

experiment 行为：

差异/异常/优势：

原因分析：

证据：

## 5. 复读/循环分析

## 6. 第一真实错误与下游症状

## 7. 最终判断

## 8. 建议验证实验或修复方向
```

## Evidence Standards

- Prefer exact paths and line references, for example `[trace.log](/abs/path/trace.log:123)`.
- Quote only short snippets needed to prove the point.
- If a conclusion is inferred, label it as inference.
- If evidence is missing, state what is missing instead of overclaiming.
