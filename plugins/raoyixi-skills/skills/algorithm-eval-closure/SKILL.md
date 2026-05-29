---
name: algorithm-eval-closure
description: Close algorithm evaluation loops by analyzing batch eval entrypoints, logs, issue resolution rates, verifier status, failure taxonomy, summary artifacts, path/env isolation, and next-step improvement plans.
---

# Algorithm Eval Closure

Use this skill for batch evaluation reports, issue resolution statistics, eval entrypoint design, c250-codex eval runs, summary artifacts, and model/system failure separation.

## Workflow

1. Map the entry chain:
   - batch script
   - wrapper script
   - agent shell
   - Python entry
   - model API layer
   - verifier/report script
2. Define success criteria:
   - internal agent success
   - verifier success
   - target issue disappeared
   - returned final answer
   - patch touches target files
   - summary artifact exists
   - shell exit code
3. Count outcomes:
   - total samples
   - internal success/failure
   - external success/failure
   - missing memory JSON
   - missing summary
   - MAX_TURNS_EXCEEDED
   - API failures
   - context overflow
   - parse failures
4. Separate failure classes:
   - model capability
   - convergence control
   - eval framework bug
   - path/env isolation
   - artifact collection
   - API/service instability
   - data/verifier mismatch
5. Produce closure plan:
   - framework fixes before retraining
   - failure-focused data set
   - next eval command
   - acceptance threshold
   - report path

## c250 Evaluation Checks

```bash
c250-exec -C /home/chehejia/cov-evalution-qwen3_6-eval-0521 'find docs/评测报告 -type f | sort'
c250-exec -C /home/chehejia/cov-evalution-qwen3_6-eval-0521 'grep -RIn "内部成功\\|MAX_TURNS_EXCEEDED\\|summary_missing\\|exit_code=0" docs logs | head -120'
```

For parallel evals, verify independent:

- MVBS working directory
- normalized error JSON
- CodeBuddy env file
- log root
- report path

## Output

```text
结论：
入口链路：
成功率口径：
失败分类：
优先修复：
下一轮评测命令：
验收标准：
```

Never report a single success rate without naming the denominator and success signal.

