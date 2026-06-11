---
name: testcase-trajectory-analysis
description: Analyze one testcase-generation RL rollout trajectory from a .txt log, .json trace, or rollout directory. Use when the user asks to inspect a single unit-test generation trajectory, recompute the testcase RL reward using testcase_reward_fn_v2, explain low reward, locate the first real failure point, identify the source root cause, and output one JSON item.
---

# Testcase Trajectory Analysis

Use this skill to analyze a single testcase-generation RL rollout trajectory. The output is one JSON object, not a batch report.

## Required Inputs

Accept one of:

- A rollout `.txt` log.
- A rollout `.json` trace.
- A rollout directory containing matching `.txt` and `.json` files.

Always pair `.txt` and `.json` when possible. If the user provides only `.json`, infer the same-stem `.txt` in the same directory. If the `.txt` file is missing, ask the user for it before making full root-cause claims. The `.txt` log is mandatory evidence for complete manual attribution.

If the user does not provide an output path, ask where to save the JSON. Do not choose a default output path silently. If the user only wants a terminal preview, print the JSON and do not write a file.

## Hard Reading Rules

You must deeply read the whole trajectory. Do not:

- Sample.
- Skip steps.
- Read only part of the rollout.
- Skim.
- Look only at reward.
- Look only at the final error.
- Look only at `.json` and ignore `.txt`.
- Scan logs mechanically without reasoning.

For long logs, use the helper script to build a factual skeleton, then read the raw `.txt` sequentially around all key steps, compile attempts, edits, repeated errors, and terminal failure.

## Reward Source

The reward must match the RL source algorithm:

```python
# rllm/rewards/testcase/reward_function.py::testcase_reward_fn_v2
reward_out = testcase_reward_fn_v2(task_info=task, memory_steps=smol_steps)
reward = reward_out.reward
```

Reference commit used by this project:

```text
smolagent_rllm_0_3 / d9f3b92917cd308720caaf0fa5be9ffca3785c3f
```

## Reward Formula

Use the same branch logic as `testcase_reward_fn_v2`.

```latex
\text{base\_reward} =
\begin{cases}
0, & \text{if } \text{compile\_success}=0 \\
0.3 \cdot \text{pass\_rate}, & \text{if } \text{compile\_success}=1 \land \text{all\_tests\_pass}=0 \\
0.3, & \text{if } \text{compile\_success}=1 \land \text{all\_tests\_pass}=1 \land \text{coverage}=\varnothing \\
0.3 + 0.7 \cdot \min(\frac{\text{coverage}}{90.0}, 1.0),
& \text{if } \text{compile\_success}=1 \land \text{all\_tests\_pass}=1 \land \text{coverage}\neq\varnothing
\end{cases}
```

```latex
\text{final\_reward} =
\begin{cases}
\text{base\_reward}, & \text{if } \text{is\_exception\_trajectory}=0 \\
\operatorname{round}(\text{base\_reward} \cdot 0.6, 4),
& \text{if } \text{is\_exception\_trajectory}=1
\end{cases}
```

Reward design:

- `base_reward`: quality score before exception discount. It reflects only final compile status, test pass rate, and coverage.
- `final_reward`: actual RL reward. Exception trajectories multiply `base_reward` by `0.6`.
- Compile failure gets `0`, because the test cannot run.
- Compile success with failed tests gets `0.3 * pass_rate`, giving partial credit below `0.3`.
- Compile success with all tests passing but no coverage gets `0.3`, the minimum usable success.
- Coverage contributes `0.7`; coverage reaches full reward at `90%`.
- Exception discount distinguishes active completion from forced termination such as max prompt length, timeout, or max turns.
- Strict success is `final_reward >= 1.0`. Do not use rollout JSON `is_correct` as the success criterion.

Implementation details:

- `_COMPILE_SUCCESS_TOKEN = "OVERALL TEST SUMMARY"`.
- `_COMPILE_FAILURE_TOKEN = "terminated with exit code [1]"`.
- Parse `TESTED`, `PASSED`, `FAILED` from the last successful compile observation.
- Parse the last coverage from `覆盖率: <number>%`.
- Preserve source rounding: branch values use `round(..., 4)` where the source does.

## Helper Script

Use the helper to produce reward facts and a JSON skeleton:

```bash
python /lpai/.codex-llm-eval-home/skills/testcase-trajectory-analysis/scripts/analyze_testcase_rollout.py \
  /abs/path/to/rollout_or_trace \
  --output /abs/path/to/output.json
```

If no output path is specified, the script prints JSON to stdout only.

The script does not replace manual reading. It only extracts factual reward/state fields. You must still read the raw `.txt` and fill root cause fields from evidence.

## Output JSON

Use this exact high-level structure. Keep field order when practical.

```json
{
  "data_uid": "...",
  "repo_name": "...",
  "function_name": "...",
  "rollout_id": "...",
  "original_reward": 0.162,
  "recomputed_reward": 0.162,
  "reward_match": true,
  "final_compile_success": true,
  "all_tests_pass": false,
  "intermediate_compile_error_count": 0,
  "compile_success_count": 1,
  "length_limit_or_context_exceeded": true,
  "termination_reason": "MAX_PROMPT_LENGTH_EXCEEDED",
  "reward_explanation": {
    "formula_version": "testcase_reward_fn_v2",
    "parse_source": "txt_reward_log",
    "compile_success": true,
    "all_tests_pass": false,
    "tested": null,
    "passed": null,
    "failed": null,
    "pass_rate": 0.9,
    "coverage": null,
    "base_reward": 0.27,
    "is_exception_trajectory": true,
    "exception_penalty_factor": 0.6,
    "final_reward": 0.162,
    "calculation": "final_reward = round(base_reward * exception_penalty_factor, 4) = round(0.27 * 0.6, 4) = 0.162",
    "plain_explanation": "最终编译成功但测试未全过，因此 base_reward=0.3*pass_rate=0.27；轨迹因 MAX_PROMPT_LENGTH_EXCEEDED 异常退出，因此乘以 0.6 得到 0.162。"
  },
  "root_cause_analysis": {
    "type": "cmock_api_contract_misuse",
    "summary": "错误理解 CMock 期望函数的参数契约",
    "reason": "第一次真实分叉发生在 mock 设计阶段，模型使用了不存在或参数类型错误的 CMock API；后续编译失败只是该错误测试代码被编译器暴露出来。",
    "not_terminal_reason": "最终报错是编译失败，但编译失败不是源头。源头是更早生成测试代码时选错 mock 契约。"
  },
  "first_failure_location": {
    "phase": "mock_design",
    "step": "Step 5",
    "explanation": "模型在该步首次生成错误的 CMock Expect 调用，调用签名与 get_ceedling_mock_functions 输出不一致；Step 5 之前的项目分析和 mock 函数读取仍是正确且可复用的。"
  },
  "final_failure_reason": "compile_failure",
  "key_evidence": [
    "Step 5 生成了 xxx_ExpectAndReturn(...)，但 get_ceedling_mock_functions 输出中不存在该签名。",
    "Step 7 编译报错指出 too few arguments to function xxx_ExpectAndReturn。",
    "Step 8-12 只反复调整 include 和局部变量，没有回到 CMock API 契约重新建模。"
  ],
  "failure_chain": [
    "误读 CMock 可用函数签名",
    "生成错误 mock 调用",
    "编译报错",
    "修复方向偏移",
    "最终失败或超长"
  ],
  "sft_fix_direction_candidate": "补充 CMock API 契约建模正例，要求先读取 mock 函数签名，再生成 Expect/Ignore/Return 调用。",
  "json_path": "...",
  "txt_path": "...",
  "token_stats_path": "..."
}
```

## Field Semantics

- `original_reward`: reward recorded in the rollout JSON or final TXT reward log.
- `recomputed_reward`: reward recomputed by the same logic as `testcase_reward_fn_v2`.
- `reward_match`: whether `original_reward` and `recomputed_reward` match after tolerance.
- `root_cause_analysis.type`: stable English category for later statistics.
- `root_cause_analysis.summary`: one Chinese sentence naming the source root cause.
- `root_cause_analysis.reason`: why that summary is the root cause.
- `root_cause_analysis.not_terminal_reason`: why the final error is only a symptom, not the source cause.
- `first_failure_location.phase`: coarse phase where the first real failure begins, such as `project_analysis`, `support_analysis`, `mock_design`, `test_generation`, `compile_fix_loop`, `coverage_improvement`, or `finalization`.
- `first_failure_location.step`: the first concrete step that introduces the source error. Everything before this step should be considered correct/reusable for this rollout. If the wrong content is generated in Step 5 and written to disk in Step 6, record `Step 5`, not `Step 5/6` or `Step 6`.
- `first_failure_location.explanation`: what wrong decision/content first appeared in that step, why earlier steps are still reusable, and why this step caused later drift.
- `final_failure_reason`: final failure mode, such as `compile_failure`, `test_failure`, `coverage_insufficient`, `length_limit_exceeded`, or `tool_or_environment_error`.
- `key_evidence`: concrete log facts proving the root cause. Include tool calls, compile errors, generated wrong code, repeated repair behavior, and success/failure divergence points.

## Manual Attribution Workflow

1. Read task metadata from JSON: `data_uid`, `repo_name`, `function_name`, target function, and trajectory reward.
2. Read the TXT from beginning to end. Track every step, tool call, generated test code, compile result, coverage result, repair action, and terminal event.
3. Recompute reward or verify the helper output.
4. Identify the first real failure location. Do not automatically use the final error.
5. Fill `root_cause_analysis` with one source root cause. Use secondary details in `failure_chain`, not as competing primary causes.
6. Fill `key_evidence` with concrete proof from the log.
7. Fill `sft_fix_direction_candidate` as an actionable data-improvement direction.

## Saving Output

If writing a JSON file:

1. Use the user-provided output path.
2. Write valid UTF-8 JSON with `ensure_ascii=False` and indentation.
3. Run `chmod -R 777 <output_dir>`.
4. If the file will be consumed by training or evaluation jobs, run `namei -l <output_path>` and check parent permissions.
