---
name: algorithm-training-debug
description: Use when debugging ML/LLM training failures, fine-tuning scripts, optimizer/config issues, checkpoint loading/saving, distributed training, OOM, NaN, convergence, or experiment reproducibility.
---

# Algorithm Training Debug

Use this skill for non-RL-specific training and fine-tuning failures.

## When to Use

- Training crashes, hangs, OOMs, produces NaN, fails to save/load checkpoint, or does not converge.
- The user asks to review training scripts, configs, launch commands, or checkpoint directories.
- The task involves PyTorch, Transformers, Accelerate, DeepSpeed, FSDP, Megatron, vLLM/SGLang inference after training, LoRA/QLoRA, or SFT.

## Required Checks

- Identify exact launch command, working directory, env vars, config file, branch/commit, and checkpoint path.
- Inspect config values that strongly affect behavior: model path, tokenizer, dataset, max length, batch size, grad accumulation, lr, scheduler, precision, optimizer, seed, save/eval steps.
- Check whether failures happen before data load, forward, backward, optimizer step, checkpoint save, eval, or inference.
- Verify checkpoint/model/tokenizer compatibility with a minimal load command.
- For distributed runs, check rank-specific logs and whether all ranks fail at the same step.

## Minimal Verifications

- One-batch or few-sample dry run.
- Config parse and model/tokenizer load.
- Dataset first N samples after preprocessing.
- Checkpoint save/load round trip if checkpointing is involved.
- Eval subset run after training script changes.

## Root Cause Categories

- Data/preprocess issue
- Config mismatch
- Precision/numerical issue
- Memory/resource issue
- Distributed/runtime issue
- Checkpoint/tokenizer mismatch
- Evaluation/inference mismatch
- Actual optimization/model limitation

## Output Format

- Training chain: command -> config -> data -> model -> output.
- Failure stage and first real error.
- Root cause table with evidence.
- Minimal patch/config change.
- Verification command and expected signal.
