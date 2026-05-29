---
name: paper-implement
description: Reproduce machine learning or AI research papers inside a given training framework. Use when the user provides a paper PDF, paper excerpts, implementation notes, reproduction documents, or zero or more auxiliary docs, and asks Codex to implement the paper algorithm in an existing framework. The skill enforces deep source reading, PLAN.md first, user review before implementation, plan revision after feedback, strict implementation against the approved plan, static algorithm validation, and smoke test scripts.
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
- static algorithm validation scan
- import validation
- config validation
- tiny data smoke test
- tiny model or mocked model smoke test
- single-step loss/reward sanity check
- short training run
- expected outputs
- failure diagnostics
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

## Phase 5: Static Error Validation

Before claiming completion, perform a static validation scan of the reproduced algorithm.

Check at minimum:

- equation-to-code correspondence
- tensor shapes
- dtype/device placement
- gradient flow
- detach/no-grad boundaries
- distributed synchronization assumptions
- config defaults
- imports
- optional dependency handling
- data field names
- missing masks
- numerical stability
- checkpoint save/load compatibility
- logging correctness

Report any remaining uncertainty explicitly.

## Phase 6: Smoke Test

Provide a small smoke test script or command.

The smoke test should verify:

- imports succeed
- config loads
- algorithm switch enables correctly
- a tiny batch can run
- loss/reward/metric values are finite
- backward compatibility path still runs when the algorithm is disabled

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
