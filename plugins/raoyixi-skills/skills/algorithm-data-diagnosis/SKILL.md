---
name: algorithm-data-diagnosis
description: Use when analyzing ML/LLM training or evaluation data quality, dataset schemas, labels, sample distribution, duplicates, leakage, train/eval drift, malformed JSON/JSONL, or failed samples.
---

# Algorithm Data Diagnosis

Use this skill to find data problems before blaming training or model capability.

## When to Use

- The user asks to analyze datasets, samples, labels, prompts, mergeKeys, JSON/JSONL, parquet/csv, or train/eval split quality.
- Training loss, evaluation score, solve rate, or model behavior looks wrong and data quality may be involved.
- The task involves data extraction, path normalization, duplicate removal, label noise, leakage, or distribution mismatch.

## Required Checks

- Identify file format, schema, row count, and key fields.
- Count missing/null/empty fields, malformed records, duplicates, and invalid paths.
- Compare train/eval/test distributions for length, label, task type, source, timestamp, and difficulty.
- Sample both successes and failures; never inspect only aggregate metrics.
- Check for leakage: identical prompts, labels, target files, or issue ids across splits.
- Validate path references exist inside the intended runtime workspace.

## Recommended Commands

- `python -m json.tool` for JSON sanity.
- Small Python scripts for row counts, key frequency, lengths, nulls, duplicates, and split overlap.
- `head`, `wc -l`, `find`, and `rg` for quick inspection.
- Use pandas/pyarrow only if the project already depends on them or the file format requires them.

## Root Cause Categories

- Schema mismatch
- Bad/missing labels
- Duplicate or leaked samples
- Distribution drift
- Malformed prompt/completion
- Invalid file paths
- Runtime data copy/isolation issue
- Eval data not aligned with training objective

## Output Format

- Dataset inventory: paths, format, counts.
- Quality findings: issue, count/rate, examples.
- Distribution findings: train vs eval differences.
- Failure linkage: which data issue explains which metric/log symptom.
- Fix plan: minimal data fix plus validation command.
