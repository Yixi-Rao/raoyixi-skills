---
name: algorithm-eval-diagnosis
description: Use when analyzing model or agent evaluation failures, solve rate, pass rate, benchmark drift, baseline comparison, eval harness bugs, scoring logic, regression tests, or release readiness.
---

# Algorithm Eval Diagnosis

Use this skill to determine whether evaluation results reflect model quality or harness/data/environment issues.

## When to Use

- The user asks why evaluation solve rate/pass rate changed.
- The task involves eval logs, failure categories, baseline vs candidate comparison, benchmark selection, or eval script changes.
- The user asks to design or repair an evaluation loop.

## Required Checks

- Identify eval entrypoint, data source, model endpoint, scoring rule, output artifacts, and report script.
- Verify the model actually called by eval matches the intended model/checkpoint.
- Compare baseline and candidate under the same data, harness version, decoding parameters, and environment.
- Inspect failed samples by category; do not rely only on aggregate pass rate.
- Distinguish model failure from data, environment, tool, timeout, parser, endpoint, and report-generation failures.
- Keep a reproducible subset command for 3-10 samples before full eval.

## Recommended Metrics

- Total, pass, fail, solve rate.
- Failure categories and counts.
- Runtime per sample and timeout rate.
- Missing artifact rate.
- API error rate.
- Parser/protocol error rate.
- Baseline delta with confidence caveats.

## Output Format

- Eval chain map.
- Metric summary.
- Failure taxonomy with examples.
- Harness issues vs model issues.
- Minimal repair and rerun command.
- Release/go-no-go recommendation.
