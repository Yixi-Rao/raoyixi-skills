---
name: algorithm-agent-trace-analysis
description: Use when analyzing agent trajectories, tool calls, JSONL logs, MAX_TURNS_EXCEEDED, output protocol failures, invalid tool arguments, environment errors, or agent evaluation traces.
---

# Algorithm Agent Trace Analysis

Use this skill to debug agent behavior from logs and traces.

## When to Use

- The user asks to analyze agent logs, trace JSON, tool calls, eval trajectories, or failed agent samples.
- Failures include MAX_TURNS_EXCEEDED, invalid format, wrong tool use, missing final answer, API errors, or environment access errors.
- The task involves coding agents, APR agents, RLLM/smolagents traces, Langfuse/Phoenix/Opik/Weave style spans, or custom agent logs.

## Required Checks

- Identify trace format, sample id, model endpoint, prompt, tool list, max turns, and final grader.
- Find the first real error, not just the last line.
- Separate agent behavior from harness/environment/API problems.
- Count repeated loops, invalid outputs, failed tool calls, timeout/API errors, and missing artifacts.
- Compare success and failure traces when available.
- Preserve sample ids and log paths for reproducibility.

## Failure Categories

- API/model service issue
- Tool protocol issue
- Tool argument/environment issue
- Planning or search loop issue
- Context/window issue
- Verification skipped or failed
- Output parser/final answer issue
- Evaluation harness/reporting issue
- Model capability issue

## c250-codex Trace Checks

When analyzing `/home/chehejia/cov-evalution` or `/home/chehejia/cov-evalution-qwen3_6-eval-0521`, check both internal and external status:

- `json-output/*_memory.json`: `execution_status`, `returned_final_answer`, termination reason.
- agent log: `MAX_TURNS_EXCEEDED`, `finish_reason=length`, parse errors, ellipsis/no-op tool calls.
- final patch: whether it touches the target source file and whether target mergeKey disappeared.
- summary: distinguish normal summary from `summary_missing.txt`.
- shell/batch status: do not trust `exit_code=0` until it matches internal status and verifier result.

Useful remote commands:

```bash
c250-exec -C /home/chehejia/cov-evalution-qwen3_6-eval-0521 'grep -RIn "MAX_TURNS_EXCEEDED\\|finish_reason=length\\|summary_missing\\|execution_status\\|exit_code=0" docs logs | head -120'
c250-exec -C /home/chehejia/cov-evalution-qwen3_6-eval-0521 'find logs -name "*_memory.json" -o -name "*.patch" | head -100'
```

## Output Format

- Trace inventory: logs, JSON, sample ids.
- Timeline of the failed sample.
- First failure and downstream symptoms.
- Category counts across samples.
- Fix plan: prompt/tool/harness/env/model.
- Regression eval to catch recurrence.
