---
name: algorithm-rl-debug
description: Use when debugging RLHF, GRPO, PPO, DPO, reward functions, rollout generation, KL, advantage, group sampling, verifier rewards, or agent RL post-training.
---

# Algorithm RL Debug

Use this skill for RL post-training and reward-driven optimization.

## When to Use

- The user mentions GRPO, PPO, DPO, RLHF, reward model, verifier reward, rollout, KL, advantage, policy/reference model, or agent RL.
- Training reward is flat/collapsed, KL explodes, output format degrades, or solve rate does not improve.
- The task involves TRL, verl, OpenRLHF, Unsloth RL, Axolotl RL, or custom reward scripts.

## Required Checks

- Inspect prompt/completion format and whether reward functions can parse model outputs.
- Unit test reward functions on handcrafted positive, negative, and malformed examples.
- Report reward distribution: min/max/mean/std, zero rate, saturation, per-component rewards.
- Check group size, sampling temperature/top_p, max tokens, stop sequences, and format constraints.
- Check KL/reference policy setup and whether tokenizer/model mismatch exists.
- Compare training reward with offline eval; reward improvement without eval improvement is suspicious.

## Common Failure Patterns

- All rewards identical: parser bug, missing ground truth, constant reward, all samples malformed.
- High reward but poor eval: reward hacking, weak verifier, leaked labels, wrong metric.
- KL explosion: low KL penalty, high lr, reward scale too large, bad reference model.
- Format collapse: reward underweights format, max tokens too small, stop sequence mismatch.
- Slow/no learning: batch too small, group sampling too narrow, reward sparse, noisy data.

## Output Format

- RL chain: data -> rollout -> reward -> advantage/KL -> update -> eval.
- Reward tests and distribution.
- Failure category and evidence.
- Minimal fix: reward/parser/config/data.
- Next run plan: one change, metric to watch, stop condition.
