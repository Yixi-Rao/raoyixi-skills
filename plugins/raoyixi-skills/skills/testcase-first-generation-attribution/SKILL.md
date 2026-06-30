---
name: testcase-first-generation-attribution
description: Attribute why a testcase-generation agent's first generated C unit test failed. Use when analyzing teacher/SFT/RL testcase logs where the user asks why the first create_new_file result did not compile, pass tests, or reach coverage threshold; classify whether the source cause is prompt design, Step 1-5 evidence/analysis failure, Step 5 design failure, final C/CMock code-generation weakness, verifier-loop policy, or tool/environment error, and produce prompt or data-improvement recommendations.
---

# Testcase First Generation Attribution

Use this skill to explain why the **first generated testcase** failed in a C/Ceedling/CMock unit-test generation trajectory.

The target question is not "why did the whole rollout finally succeed or fail". The target question is:

```text
After the first test file was generated, why did the first compile/test/coverage check fail
or fail to reach the target coverage?
```

## Core Rule

Use the first-generation cutoff:

1. Find the first `create_new_file(...)` that writes `test/test_*.c` or `test_*.c`.
2. Find the first `compile_ceedling_repo(...)` after that file creation.
3. If compile/test passes, find the first `get_coverage_report(...)`.
4. Judge only this first generated test and first verification result.
5. Use later repair steps only as diagnostic evidence for what the first generation lacked.

Do not attribute based on the final repaired test unless the question explicitly asks about repair quality.

## Required Evidence

Read the raw log around all of these sections:

- Original prompt / guidance at the top of the run.
- Step 1 function-body evidence.
- Step 2 support / fixture evidence.
- Step 3 CMock API evidence.
- Step 4 conditional-compile evidence.
- Step 5 design review, if present.
- First generated test code.
- First compile/test result.
- First coverage result, if compile/test passed.
- Later successful repair, if any, only to identify the missing first-pass insight.

If the user provides a `.json` trace, pair it with the `.txt` log when possible. Do not make full root-cause claims from JSON alone when the text log exists.

## Attribution Decision Tree

Use one primary category. Secondary factors may be listed separately.

### 1. `prompt_design_issue`

Use when the prompt did not require or did not clearly enforce the behavior needed for first-pass success.

Examples:

- Prompt asks to generate tests but does not require stopping after first verification for teacher data synthesis.
- Prompt requires CMock table but does not require handling dynamic pointer/output-parameter cases.
- Prompt has no fewshot for a recurring pattern such as local pointer output through `mvbs_memcpy(&local, &arg, sizeof(ptr))`.
- Prompt says "use CMock API" but does not require checking whether a chosen API exists in Step 3.
- Prompt allows broad repair loops when the experiment wants first-pass-only data.

Recommendation style:

- Add a concrete rule.
- Add a positive fewshot.
- Add an anti-pattern fewshot.
- Add a hard stop condition if needed.

### 2. `evidence_acquisition_issue`

Use when the model did not obtain required evidence before generating code.

Examples:

- It skipped `get_ceedling_mock_functions`.
- It did not read the support header that defines the needed struct.
- It did not call `get_function_conditional_micro` when macros matter.
- The tool output was truncated or hidden and the model had insufficient information.

This can be a prompt issue if the prompt did not require the missing evidence. It is an agent execution/compliance issue if the prompt required it and the model skipped it.

### 3. `analysis_interpretation_issue`

Use when the needed evidence was present, but the model interpreted it incorrectly.

Subtypes:

- `ignored_visible_evidence`: Evidence was explicit and easy, but the model contradicted it. This is a prompt-following / attention / discipline failure.
- `subtle_c_reasoning_gap`: Evidence was present but required nontrivial C reasoning, pointer reasoning, CMock semantics, struct layout judgment, or Ceedling behavior. This is a capability gap, not merely "not careful".
- `conflicting_evidence_not_resolved`: Step 1 and Step 3 appear to conflict, and the model failed to reconcile them.

Avoid vague labels like "not serious". Say exactly what evidence was missed or misread.

### 4. `step5_design_issue`

Use when Step 1-4 evidence was mostly correct, but Step 5 produced an incomplete or wrong test design.

Examples:

- Branch coverage table includes correct branches but mock strategy table is too shallow.
- It says "Expect + ReturnThruPtr" without specifying dynamic pointer matching constraints.
- It chooses a NULL test for a function with no NULL guard.
- It claims a fixture is legal without evidence from support files.

This category means the model can gather evidence but cannot reliably convert evidence into an executable test plan.

### 5. `code_translation_issue`

Use when Step 5 plan is correct, but the generated C code contradicts or fails to implement the plan.

Examples:

- Step 5 says use `mvbs_memcpy_Stub`, but generated code uses `mvbs_memcpy_Expect(NULL, NULL, ...)`.
- Step 5 says include `mock_external_function.h`, but code omits it.
- Step 5 correctly names a CMock API, but code calls a non-existent variant.
- Step 5 fixture plan is legal, but C code initializes the wrong field.

This is final code-generation weakness, not prompt design, unless the prompt lacks a required code-generation constraint.

### 6. `verifier_loop_policy_issue`

Use when the first-generation result was evaluated, but the system kept repairing although the experiment needs first-pass data.

Examples:

- First compile fails, then the model edits repeatedly until success.
- Teacher data synthesis should stop after first verification, but the agent continues repair.

This is a pipeline/prompt stop-condition issue. It does not explain why the first code was wrong; it explains why the run did not terminate at the intended cutoff.

### 7. `tool_or_environment_issue`

Use when the first generation is not fairly judged because of external failure.

Examples:

- Tool crashes.
- Repository path is wrong.
- Permission error.
- Build system unavailable.
- Compile timeout unrelated to generated code.

Do not mix this with model capability issues.

## Judgment Procedure

### Step A: Build the first-pass timeline

Create this factual sequence:

```text
prompt constraints ->
Step 1 evidence ->
Step 2 evidence ->
Step 3 evidence ->
Step 4 evidence ->
Step 5 plan ->
first create_new_file ->
first compile/test ->
first coverage if any ->
later repair insight if any
```

For each item, record line references or exact log snippets.

### Step B: Compare evidence, plan, code, and verifier

Ask these questions in order:

1. Did the prompt require the needed behavior?
2. Did the model obtain the evidence needed for that behavior?
3. Did the model correctly interpret that evidence?
4. Did Step 5 convert the evidence into a precise executable test design?
5. Did the generated C code faithfully implement Step 5?
6. Did the first verifier failure match the suspected defect?
7. Did later repair reveal the missing insight?

The earliest "no" that explains the first verifier failure is usually the primary source cause.

### Step C: Distinguish prompt weakness from model weakness

Use this rule:

- If the prompt never required a needed behavior, or gave no reusable pattern for a high-frequency difficult case, mark `prompt_design_issue`.
- If the prompt required it and the evidence was visible, but the model did not use it, mark `analysis_interpretation_issue` or `step5_design_issue`.
- If Step 5 was right and only code was wrong, mark `code_translation_issue`.
- If the first failure was expected but the system continued repair, add `verifier_loop_policy_issue` as secondary.

### Step D: Explain "why analysis went wrong"

Do not write "不认真" by itself. Choose a precise explanation:

- `visible_evidence_ignored`: The model had direct evidence but failed to bind it into the plan.
- `missing_inference_pattern`: The model lacked a reusable reasoning pattern, such as dynamic stack-address matching in CMock.
- `overgeneralized_template`: The model copied a standard mock template into a case that violates template assumptions.
- `tool_output_underused`: The model called the right tool but did not use the exact API list or constraints.
- `insufficient_prompt_scaffold`: The prompt did not force the missing intermediate table/check.
- `code_synthesis_slippage`: The plan was right, but code emitted a different implementation.

## Output Format

Answer in Chinese unless the user asks otherwise. Keep the output concise but evidence-backed.

Use this structure:

```markdown
**结论**
首次生成失败的主因：<primary_category>
一句话根因：<root cause sentence>

**首次失败链路**
- 首次生成位置：Step X / log line ...
- 首次检测位置：Step Y / log line ...
- 首次检测结果：compile/test/coverage ...
- 直接失败原因：...

**归因判断**
- Prompt 是否有问题：是/否/部分
- Step 1-4 分析是否有误：是/否/部分
- Step 5 设计是否有误：是/否/部分
- 最终代码落地能力是否有误：是/否/部分
- 是否存在 verifier/停止策略问题：是/否/部分

**证据**
1. ...
2. ...
3. ...

**为什么不是其他原因**
- 不是 prompt 问题，因为...
- 不是纯代码能力问题，因为...
- 不是环境问题，因为...

**改进建议**
- Prompt 改法：...
- Fewshot 改法：...
- Step 5 模板改法：...
- 数据筛选/流程改法：...
```

If returning JSON is requested, use:

```json
{
  "data_uid": "...",
  "function_name": "...",
  "first_generation": {
    "create_step": "Step 8",
    "compile_step": "Step 9",
    "coverage_step": null,
    "compile_success": false,
    "tests_passed": false,
    "coverage": null
  },
  "primary_category": "step5_design_issue",
  "root_cause": "...",
  "prompt_issue": {
    "has_issue": true,
    "details": "...",
    "improvement": "..."
  },
  "analysis_issue": {
    "has_issue": true,
    "phase": "Step 5",
    "why": "missing_inference_pattern",
    "details": "..."
  },
  "code_issue": {
    "has_issue": true,
    "details": "..."
  },
  "verifier_loop_policy_issue": {
    "has_issue": true,
    "details": "..."
  },
  "evidence": ["..."],
  "recommended_actions": ["..."]
}
```

## Domain Heuristics

Common testcase first-generation failure patterns:

- CMock dynamic pointer/output-parameter mismatch:
  - Example: code calls `mvbs_memcpy(&send_buf, &buf, sizeof(char *))`.
  - `&send_buf` and `&buf` are runtime stack addresses.
  - A naive `Expect(NULL, NULL, ...)` will fail.
  - A robust first-pass plan should use a legal Stub/Callback pattern if allowed by Step 3, or explicitly avoid strict address matching.
- Non-existent CMock API:
  - Treat as Step 3 underuse or code translation issue depending on whether Step 5 listed the correct API.
- Internal vs external dependency confusion:
  - If Step 3 exposes a mock API for a function, Step 5 must reconcile that with Step 1's internal/external judgment.
- Private struct / header modeling:
  - If support files do not expose a field/type, generated test code must not invent it.
- NULL tests:
  - Only include NULL input tests when Step 1 shows a guard or safe behavior.
- Coverage shortfall:
  - If compile/test passes but coverage is low, check whether Step 5 omitted a branch, declared a branch untestable without evidence, or failed to design required mock return sequences.

## Improvement Recommendation Rules

For `prompt_design_issue`, recommend one or more of:

- Add a hard checklist item before code generation.
- Add a table column to Step 5.
- Add a positive fewshot for the failure pattern.
- Add a negative fewshot showing the bad pattern and correction.
- Add a hard stop after first verification for teacher data synthesis.

For `analysis_interpretation_issue`, recommend:

- Add focused SFT samples that teach the missing inference.
- Add verifier feedback examples that show how the compile error maps back to the evidence.
- Add a prompt micro-check only if the mistake is high frequency.

For `code_translation_issue`, recommend:

- Add paired examples where Step 5 plan is converted into exact C/CMock code.
- Add a self-check that every generated CMock call appears in Step 3 or follows an explicitly allowed callback API.

For `verifier_loop_policy_issue`, recommend:

- Modify outer pipeline or prompt to stop after first compile/test/coverage.
- Save first-pass manifest fields: first code, first verifier result, later repair success, and repair delta.
