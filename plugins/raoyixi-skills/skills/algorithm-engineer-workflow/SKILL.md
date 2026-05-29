---
name: algorithm-engineer-workflow
description: Use when the user asks for algorithm engineer work involving ML data, training, TensorBoard, checkpoints, evaluation, RL/GRPO, model quality, or experiment optimization. Orchestrates the focused algorithm skills and enforces evidence-first analysis.
---

# Algorithm Engineer Workflow

Use this skill as the top-level operating mode for algorithm engineering tasks.

For role-level constraints and c250-codex evaluation conventions, read `references/AlgoRole.md` when the user asks for an algorithm engineer role, c250 evaluation diagnosis, or a task spanning multiple algorithm work stages.

## When to Use

- The user asks to analyze or debug model training, fine-tuning, RLHF/GRPO, evaluation, TensorBoard, datasets, checkpoints, or model quality.
- The task spans multiple algorithm work stages: data -> training -> checkpoint -> evaluation -> failure analysis -> next experiment.
- The user asks for an algorithm engineer role, plan, review, diagnosis, or optimization loop.

## Core Constraints

- Do not diagnose model capability before checking data, config, environment, runtime logs, and evaluation protocol.
- Separate root causes into: data issue, training config issue, runtime/environment issue, evaluation harness issue, inference/deployment mismatch, model capability issue, and unknown.
- Prefer executable checks over narrative judgment: small sample dry-runs, schema checks, metric extraction, TensorBoard scalar inspection, checkpoint/config loading, and eval subset reruns.
- Preserve reproducibility: record data paths, code branch, commit/worktree, command, env vars, checkpoint path, eval set, metric definition, and output path.
- For repo-wide algorithm analysis, check `docs/总结/*.md` first and update durable findings there when appropriate.
- For Li Auto/lixiang Python repositories, prefer `uv` when running Python tooling unless the local project clearly uses another runner.
- Avoid raw secret or token output. Redact API keys and private endpoint credentials from summaries.

## Skill Routing

- Data/schema/sample problems: use `algorithm-data-diagnosis`.
- TensorBoard or metric curve interpretation: use `algorithm-tensorboard-analysis`.
- Training failure, checkpoint, optimizer, memory, distributed issues: use `algorithm-training-debug`.
- RLHF/GRPO/DPO/reward/rollout/KL issues: use `algorithm-rl-debug`.
- Eval harness, solve rate, regression, baseline comparison: use `algorithm-eval-diagnosis`.
- Batch evaluation closure, c250-codex reports, success-rate denominators, summary/patch/verifier consistency: use `algorithm-eval-closure`.
- Agent logs, tool calls, trajectories, MAX_TURNS, output protocol: use `algorithm-agent-trace-analysis`.

Use multiple focused skills when evidence spans layers. Typical combinations:

- Failed agent batch eval: `algorithm-eval-closure` + `algorithm-agent-trace-analysis`.
- Low solve rate with bad samples: `algorithm-eval-diagnosis` + `algorithm-data-diagnosis`.
- Training degraded after new data: `algorithm-training-debug` + `algorithm-data-diagnosis` + `algorithm-tensorboard-analysis`.
- GRPO instability: `algorithm-rl-debug` + `algorithm-tensorboard-analysis` + `algorithm-agent-trace-analysis`.

## Standard Workflow

1. Identify the exact entrypoint script or command.
2. Map inputs and outputs: data, config, checkpoint, logs, TensorBoard event files, eval results.
3. Run or propose the smallest verification command that can reproduce the issue.
4. Classify failures with evidence and file/line/log references.
5. Propose minimal fixes, then a safer long-term loop if the issue is systemic.
6. End with the next experiment plan: command, expected signal, success threshold, and residual risk.

## Output Format

- Scope: target repo, scripts, data, checkpoint, eval artifacts.
- Evidence: metrics/logs/files inspected.
- Root Cause Table: category, evidence, confidence, fix.
- Minimal Fix: smallest code/config/data change.
- Verification: commands and expected results.
- Next Iteration: one or two concrete experiments.
