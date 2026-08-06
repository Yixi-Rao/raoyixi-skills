---
name: paper-implement
description: "Reproduce machine learning or AI research papers inside a given training framework. Use when the user provides a paper PDF, paper excerpts, implementation notes, reproduction documents, or auxiliary docs and asks Codex to implement the paper algorithm in an existing framework. Enforce deep source reading, PLAN.md first, user review before implementation, approved-plan changes only, and three-layer validation: formula unit/fuzz tests, framework integration tests, and default-off no-side-effect invariants."
---

# Paper Implement

Use this skill to reproduce a research paper in a specified training framework.

The workflow is intentionally gated: first read, then plan, then get user approval, then implement. Do not skip the planning gate.

## Core Rules

- Address the user according to the active repository or conversation instructions.
- Treat the paper, provided excerpts, reproduction notes, framework source code, configs, and scripts as primary evidence.
- Read the paper and all provided documents carefully, deeply, responsibly, comprehensively, and line by line where text is available.
- Do not rely on memory for implementation decisions. If the user asks a question or proposes a change during plan review, inspect the relevant paper text and framework source code again before answering.
- Do not implement before the user approves the plan.
- If implementation reveals an unexpected issue not covered by the approved plan, stop broad implementation and create a new plan document describing the issue, options, risks, and recommended resolution.
- Keep changes scoped to the paper reproduction and the target training framework.
- Treat a full training run as experimental evaluation, not as a substitute for formula, integration, or compatibility verification.

## Inputs

Expect some or all of:

- A paper PDF, paper excerpt, arXiv link, local PDF path, or pasted paper section.
- Zero or more reproduction notes, prior implementations, blog posts, configs, issue threads, or experiment logs.
- A target training framework or repo path.
- Optional target model, dataset, launcher, distributed runtime, hardware constraints, and expected output metrics.

If any critical input is missing, infer conservatively only when safe. Otherwise ask a concise clarification before planning.

## Phase 1: Evidence Reading

Before writing any plan:

1. Extract readable text from PDFs or provided paper sections.
2. Read all provided documents line by line where possible.
3. Inspect the target training framework source code, not only README files.
4. Identify the exact framework extension points:
   - trainers
   - losses
   - rollout logic
   - data loaders
   - model wrappers
   - config system
   - launch scripts
   - logging and metric code
   - checkpointing and resume behavior
5. Build a paper-to-code mapping:
   - paper algorithm component
   - required inputs and outputs
   - current framework location
   - required code change
   - compatibility risk
   - validation method

Do not summarize from memory. Use source-grounded findings.

## Phase 2: Create PLAN.md First

Before implementation, create a repo-local `PLAN.md` or a clearly named plan file such as:

```text
<PAPER_NAME>-Implementation-Plan.md
```

The plan must be detailed enough for the user to audit before code is changed.

Use this structure unless the user requests another format:

```markdown
# <Paper Name> Implementation Plan

## 目录

1. [<Paper Name> 原理回顾](#1-paper-name-原理回顾)
2. [<Training Framework> 框架架构分析](#2-training-framework-框架架构分析)
3. [可行性评估](#3-可行性评估)
4. [风险与不确定性（完整版）](#4-风险与不确定性完整版)
5. [详细实现方案](#5-详细实现方案)
6. [代码实现细节](#6-代码实现细节)
7. [sh 脚本控制方案](#7-sh-脚本控制方案)
8. [Tensorboard 指标方案](#8-tensorboard-指标方案)
9. [验证计划](#9-验证计划)

## 1. <Paper Name> 原理回顾

Explain the paper algorithm from the source text.

Include:
- core objective
- loss function or reward definition
- data assumptions
- training schedule
- inference or rollout behavior
- important equations
- implementation-sensitive details
- what is mandatory vs optional

## 2. <Training Framework> 框架架构分析

Explain the actual framework code path.

Include:
- current trainer flow
- config loading and override mechanism
- model construction
- data pipeline
- loss or reward calculation
- distributed execution path
- checkpointing
- logging
- launch scripts
- relevant file paths and functions

## 3. 可行性评估

Give a direct feasibility judgment.

Cover:
- whether the algorithm can be implemented in this framework
- required invasiveness
- expected code locations
- expected compatibility with existing configs
- expected compatibility with existing models
- expected compatibility with existing datasets
- expected runtime or distributed-training constraints
- minimum viable reproduction scope

## 4. 风险与不确定性（完整版）

List all material risks.

Must include:
- paper ambiguity
- missing hyperparameters
- equation-to-code translation risks
- framework API risks
- config compatibility risks
- import compatibility risks
- data compatibility risks
- tensor shape and dtype risks
- distributed training risks
- checkpoint compatibility risks
- logging and metric interpretation risks
- reproducibility risks
- performance risks
- smoke-test limitations

For each risk, include:
- evidence
- impact
- mitigation
- validation method

## 5. 详细实现方案

Describe the implementation in execution order.

Include:
- new modules/classes/functions
- modified modules/classes/functions
- config additions
- backward compatibility behavior
- default-off switches
- data format expectations
- training script changes
- metric additions
- fallback behavior

## 6. 代码实现细节

Give concrete code-level design.

For each file:
- path
- reason for change
- exact function/class to edit
- expected logic
- inputs and outputs
- edge cases
- tests or checks

## 7. sh 脚本控制方案

Describe launcher changes.

Include:
- new environment variables
- new config overrides
- example command
- default values
- how to turn the paper algorithm on/off
- compatibility with existing scripts

## 8. Tensorboard 指标方案

Define metrics.

Include:
- metric name
- formula
- logging location
- expected range
- debugging interpretation
- relation to paper claims

## 9. 验证计划

Include:
- formula unit and fuzz-test matrix
- framework integration-test matrix
- default-off no-side-effect invariants
- import/config validation and a tiny-batch smoke test
- expected outputs, tolerances, and failure diagnostics

Also include a dedicated subsection:

### 三层可证伪验证

#### 1. 算法核心公式：单元测试与模糊测试
- Map every distinctive paper formula to the target function, its inputs/outputs, and an independent test-side reference calculation. Do not derive expected values from the implementation under test.
- Define deterministic fixtures: normal, boundary, degenerate, and invalid inputs. Cover thresholds, clipping, masks, padding, empty valid tokens, shapes, dtypes/devices, NaN/Inf, and algorithm-specific conditions such as ratio=1 or unit weights.
- Compute expected values from the formula, then compare the training-framework function output to them with a stated tolerance. Include official examples, golden fixtures, or parity checks when available.
- Add fuzz tests that vary shapes, mask layouts, numerical ranges, and relevant config combinations. Preserve a seed and a minimized failing case for every failure.
- State the failure oracle: report the formula term, fixture or fuzz seed, expected value, actual value, and the first divergent tensor/index.

#### 2. 训练框架集成测试
- Test the reproduced module together with its real framework seams: upstream data loader/rollout/logprobs/rewards/advantages/masks and downstream trainer/loss aggregation/backward/optimizer/logging/checkpoint paths.
- Define the contract at each seam: field names, shape, dtype, device, batch/sequence semantics, mutability, and distributed assumptions.
- Run a minimal end-to-end training closure using a real or controlled mini batch: data preparation → forward → new algorithm module → loss → backward → optimizer step → metrics → checkpoint save/load.
- Cover the framework modes that the plan claims to support, such as single/multi-GPU, mixed precision, gradient accumulation, and resume training. Verify that the algorithm switch reaches the real training path.

#### 3. 副作用不变量检查
- With the reproduced method disabled, compare the original framework and new code on identical model weights, batch, rollout, seed, and config. Old outputs must remain identical or within a stated tolerance.
- Compare at least the old loss/reward/KL/entropy, masks and valid-token counts, key intermediate tensors, gradients, optimizer-step parameters/state, and existing metric meanings.
- Verify that the new method does not silently mutate original input tensors/files, existing configs, data schemas, checkpoint formats, launch behavior, or old training/evaluation paths.
- Add enabled-path degeneracy tests whenever the formula permits it. For example, ratio=1 should recover the original online PG/GRPO behavior; identical replay and online routing should add no difference.
- Record the fixture, command, tolerance, maximum observed difference, and failure attribution for every invariant.
```

## Phase 3: User Review Gate

After creating the plan:

1. Present the plan path and a concise summary.
2. Ask the user to review it.
3. Ask whether they approve implementation or want changes.
4. Do not proceed to implementation until the user explicitly approves.

If the user proposes changes:

1. Re-read the relevant paper sections and source files.
2. Update the plan based on evidence.
3. Explain what changed and why.
4. Ask for approval again.

## Phase 4: Implement Only After Approval

After approval:

1. Implement strictly according to the approved plan.
2. Keep the algorithm default-off unless the plan explicitly says otherwise.
3. Preserve backward compatibility for existing training configs and scripts.
4. Add config switches for the reproduced method.
5. Add metrics needed to debug correctness.
6. Avoid unrelated refactors.
7. Do not silently change data contracts, import paths, checkpoint formats, or launcher behavior.

If a previously unknown problem appears:

1. Stop expanding the implementation.
2. Create a new plan document, for example:

```text
<PAPER_NAME>-Implementation-Plan-Update-<N>.md
```

3. Document:
   - what was discovered
   - why the approved plan is insufficient
   - affected files
   - possible solutions
   - risks
   - recommendation
4. Ask the user before continuing.

## Phase 5: Three-Layer Validation

Before claiming completion, execute the three layers below. Passing a long training run does not replace any of them.

### 5.1 Formula Unit and Fuzz Tests

1. Build an independent reference calculation for every distinctive algorithm formula.
2. Turn representative formula inputs and expected outputs into unit tests for the reproduced framework function.
3. Cover normal, boundary, degenerate, and invalid cases; include algorithm-specific null/identity cases and tensor-contract checks.
4. Add seeded fuzz tests across shapes, masks, numeric ranges, and relevant config combinations.
5. On failure, retain a reproducible fixture or seed and report expected/actual values plus the divergent formula term.

### 5.2 Training-Framework Integration Tests

1. Exercise the reproduced module with its actual upstream and downstream framework modules.
2. Verify field contracts, tensor semantics, gradient flow, config propagation, logging, checkpointing, and relevant distributed assumptions at each seam.
3. Run a minimal training closure through data preparation, forward, loss, backward, optimizer step, metrics, and checkpoint save/load.
4. Cover every runtime mode claimed in the plan; do not claim untested modes as supported.

### 5.3 No-Side-Effect Invariants

1. With the algorithm disabled, compare new code against the original framework using identical weights, inputs, rollout, seed, and config.
2. Require old outputs, metrics, gradients, and optimizer behavior to remain identical or within an explicit floating-point tolerance.
3. Verify that inputs, old configs, metric meanings, data schemas, checkpoints, launchers, and old training/evaluation paths are not silently changed.
4. Test enabled-path identity cases that should reduce to the baseline whenever the formula defines one.

Report commands, fixtures, seeds, tolerances, maximum differences, failures, and remaining uncertainty explicitly.

## Phase 6: Smoke Test

Provide a small smoke test script or command.

The smoke test should verify:

- imports succeed
- config loads
- algorithm switch enables correctly
- a tiny batch can run
- loss/reward/metric values are finite
- at least one formula unit test and one seeded fuzz case pass
- one framework integration closure reaches optimizer step and checkpoint save/load
- the disabled path and one enabled-path identity case satisfy the planned invariants

Prefer a script such as:

```text
scripts/smoke_test_<paper_name>.py
```

or a minimal shell command if that matches the repo style better.

Do not present a full expensive training run as the only validation path.

## Completion Response

When done, report:

- plan file path
- files changed
- validation commands run
- smoke test location
- known limitations
- any remaining risks

Keep the final response concise but source-grounded.
