---
name: algorithm-tensorboard-analysis
description: Use when the user asks to analyze TensorBoard event files, scalar curves, loss/reward/KL/lr/grad_norm/eval metrics, convergence, overfitting, instability, or training health.
---

# Algorithm TensorBoard Analysis

Use this skill to turn TensorBoard curves into concrete training diagnoses.

## When to Use

- The user asks to read TensorBoard, event files, training curves, or scalar metrics.
- The issue involves loss spikes, reward collapse, KL explosion, learning-rate schedule, eval degradation, gradient norm, throughput, or convergence.
- The user wants to compare baseline vs new run.

## Required Checks

- Locate event files and map run directory names to model/config/checkpoint.
- Extract scalar tags and select relevant ones before interpreting curves.
- Compare steps by aligned global step, not wall-clock time, unless throughput is the question.
- Check train and eval metrics together; a falling train loss alone is not success.
- Look for restarts, missing steps, duplicated steps, logging gaps, and changed metric names.
- Link curve anomalies back to config changes, data changes, checkpoint resume, or eval harness changes.

## Recommended Commands

Use TensorBoard's event accumulator when available:

```python
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
ea = EventAccumulator(event_dir)
ea.Reload()
print(ea.Tags()["scalars"])
```

If TensorBoard is not installed, inspect the project dependency files before adding it.

## Diagnosis Guide

- Train loss down, eval flat/down: possible overfit, eval mismatch, label leakage, or wrong eval metric.
- Loss/reward NaN: check lr, bf16/fp16, grad clipping, data outliers, reward values.
- KL explosion: reward too strong, KL coef too low, reference/policy mismatch, bad initialization.
- Reward flat: reward function broken, all-zero labels, parser mismatch, no learning signal.
- Grad norm spikes: bad batch, lr too high, mixed precision, optimizer state resume issue.
- Throughput drop: dataloader, checkpointing, GPU memory, distributed stragglers.

## Output Format

- Event files inspected and scalar tags used.
- Metric timeline with key step ranges.
- Anomaly table: symptom, step range, likely cause, evidence.
- Recommended next run: minimal config/data change and expected curve movement.
