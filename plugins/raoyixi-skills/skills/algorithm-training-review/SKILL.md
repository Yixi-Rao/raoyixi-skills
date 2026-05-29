---
name: algorithm-training-review
description: Review algorithm training workflows, training scripts, TensorBoard metrics, checkpoints, reward functions, GRPO/RL logs, model conversion, deployment paths, and training-effect improvement plans.
---

# Algorithm Training Review

Use this skill for training scripts, TensorBoard, GRPO/RL debug, checkpoint lineage, reward functions, model conversion, inference deployment, and training-effect improvement.

## Workflow

1. Locate the training chain:
   - data path
   - training entry script
   - config file
   - base model
   - output checkpoint
   - conversion script
   - deployment path
   - evaluation script
2. Inspect training signals:
   - train/loss
   - eval/loss
   - learning rate
   - grad norm
   - sequence length
   - throughput
   - reward mean/std
   - KL
   - success rate
3. Classify symptoms:
   - data format mismatch
   - reward hacking or sparse reward
   - overfitting
   - underfitting
   - unstable LR
   - context truncation
   - checkpoint path mismatch
   - deployment config mismatch
4. Verify minimally:
   - compile/import changed scripts
   - run small data dry-run
   - test reward function on fixed examples
   - load model config
   - run small eval subset
5. Recommend next experiment:
   - exact config delta
   - expected metric movement
   - stopping condition
   - rollback criterion

## Minimal Checks

```bash
python -m py_compile <training_script.py>
python - <<'PY'
from transformers import AutoConfig
cfg = AutoConfig.from_pretrained("<model_dir>", trust_remote_code=True)
print(type(cfg).__name__, getattr(cfg, "model_type", None))
PY
```

For TensorBoard, first list event tags before interpreting:

```bash
python - <<'PY'
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
ea = EventAccumulator("<event_dir>")
ea.Reload()
print(ea.Tags())
PY
```

## Output

```text
训练链路：
指标事实：
问题分层：
最小实验：
验证命令：
风险：
```

Do not recommend large retraining before checking data, reward, checkpoint, and evaluation path integrity.

