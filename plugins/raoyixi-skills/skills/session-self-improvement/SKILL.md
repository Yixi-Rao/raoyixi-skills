---
name: session-self-improvement
description: Review the current Codex session or a proposed idea/information dimension to decide whether it deserves updates to user-level constraints, rules, AGENTS.md, memory, or skills. Use contradiction-analysis and criticism-self-criticism to weigh durable value against negative side effects before applying narrow improvements.
---

# Session Self Improvement

## Purpose

Run a deliberate self-improvement pass over the whole available session, or evaluate a specific idea/information dimension for whether it should change user-level constraints, rules, `AGENTS.md`, memory, or skills. Treat the compacted summary, visible messages, tool results, user corrections, and final outcomes as evidence. Convert only durable, net-positive lessons into memory, constraints, or skill changes.

This is the authoritative self-improvement entrypoint. The older `self-improving-agent` skill is retained only as a compatibility alias; reusable concepts from it now live here as reference material.

This skill coordinates existing capabilities:

- `continuous-learning-v2`: express lessons as atomic instincts or reviewable learning candidates.
- `agent-memory-mcp`: persist reusable decisions, patterns, bugs, and preferences through MCP memory tools.
- `skill-creator`: create or revise skills when the lesson is procedural and reusable.
- `contradiction-analysis`: identify competing forces, the principal contradiction, and what kind of update would resolve it.
- `criticism-self-criticism`: review the proposed update for evidence quality, overreach, maintenance burden, and unintended harm.
- `codex-hooks`: use only when the improvement is specifically about Codex hook configuration.

## Workflow

1. Reconstruct available context.
   - Include all visible conversation.
   - Include any compaction summary as first-class evidence.
   - Include local artifacts created during the session when they are relevant.
   - Do not assume unavailable pre-compact details beyond the summary.

2. Extract candidates.
   - User corrections: what the user explicitly said was wrong or preferred.
   - Agent errors: unnecessary actions, wrong skill choice, unsafe assumption, weak verification, or avoidable friction.
   - Durable preferences: stable ways the user wants work done.
   - Project rules: constraints specific to a repo or workflow.
   - Skill gaps: missing trigger rules, missing guardrails, or repeated manual patterns.
   - Proposed idea or information dimension: the user may ask whether some new rule, fact, framework, preference, or workflow should affect future behavior.

3. Evaluate necessity and side effects before classifying.
   - Use `contradiction-analysis` for non-trivial candidates. List the competing forces, identify the principal contradiction, decide whether it is global or local, and select a response.
   - Use `criticism-self-criticism` to review the proposed update before writing it. Ask what could go wrong, what evidence is missing, what maintenance burden it creates, and whether it duplicates existing rules.
   - Compare expected value against negative impact: better future behavior, fewer repeated errors, clearer routing, and safer defaults versus context bloat, stale rules, overfitting, conflicts, privacy risk, and extra maintenance.
   - For non-trivial learning updates, use the memory model in `references/self-improvement-memory-model.md` to separate semantic patterns, episodic evidence, and working-session context.
   - Skip or defer updates when the value is speculative, the evidence is weak, the scope is unclear, or the negative side effects exceed the benefit.

4. Classify each candidate only after the necessity gate.
   - `memory`: reusable fact, preference, decision, or failure mode.
   - `AGENTS.md`: broad operating constraint that should affect most future work.
   - `rules`: user-level or tool-specific rule files when the lesson is stable but belongs outside `AGENTS.md`.
   - `MCP memory`: durable structured facts, decisions, patterns, bugs, and preferences.
   - `Obsidian knowledge base`: human-readable linked notes, session retrospectives, daily logs, and vault-managed knowledge.
   - `existing skill`: a specific skill needs clearer trigger rules, workflow, or safety checks.
   - `new skill`: a repeated workflow deserves a dedicated skill.
   - `no action`: too transient, speculative, secret-bearing, or insufficiently evidenced.

5. Apply changes narrowly.
   - Write memories with `agentMemory` MCP tools when available.
   - Use Obsidian skills when the user wants a human-readable knowledge base, linked notes, or vault content.
   - For continuous-learning-v2, prefer reviewable candidates or atomic instincts over broad prose.
   - Edit existing skills only when the gap is clearly tied to that skill.
   - Create a new skill only when no existing skill owns the workflow.
   - Update `AGENTS.md` only for stable, global constraints, not one-off task logs.
   - Update user-level rules only when they are stable, actionable, and have a clearly bounded trigger.
   - When the target might be `AGENTS.md`, apply the `AGENTS.md Update Standard` below before editing.
   - When changing a skill because of a lesson, use `references/evolution-markers.md` to record why the change is justified and whether it is a correction, pattern extraction, or governance update.

6. Validate.
   - Validate JSON/YAML or skill structure after edits.
   - Run `quick_validate.py` for created or substantially modified skills.
   - Report what changed, what was intentionally not persisted, and any blocked writes.

## Necessity Gate

Before changing user-level constraints, rules, `AGENTS.md`, memory, or skills, answer these questions for each candidate:

| Question | Persist only if |
| --- | --- |
| Evidence | The lesson is backed by user correction, repeated friction, verified behavior, or a clear recurring workflow. |
| Durability | The lesson is likely to matter across future sessions or across a defined project/workflow. |
| Actionability | The update changes a concrete future behavior, trigger, routing decision, or safety check. |
| Scope | The target is clear: memory, AGENTS.md, rules, existing skill, new skill, hook, or no action. |
| Positive value | The update reduces repeated errors, improves judgment, clarifies ownership, or prevents risky behavior. |
| Negative impact | Context bloat, stale instructions, conflicts, privacy risk, maintenance cost, and overfitting are acceptable. |
| Duplication | No stronger existing rule, memory, or skill already covers it. |

If any answer is uncertain, prefer `memory` or `no action` over editing global constraints. If the candidate is useful but not yet proven, store it as a reviewable learning candidate instead of a hard rule.

## Contradiction And Criticism Review

For non-trivial updates, produce a short internal or visible review before applying changes:

```text
Candidate: <idea or information dimension>
Contradictions:
- <future usefulness> vs <context bloat / maintenance>
- <global consistency> vs <local specificity>
- <automation benefit> vs <side-effect or privacy risk>
Principal contradiction: <one sentence>
Criticism/self-criticism:
- Evidence weakness: <...>
- Possible harm: <...>
- Duplication/conflict: <...>
- Narrowest safe target: <memory | AGENTS.md | rules | existing skill | new skill | no action>
Decision: <persist | defer | skip> because <...>
```

The final decision should be conservative: improve future behavior while minimizing always-on context and irreversible side effects.

## AGENTS.md Update Standard

Use this standard when deciding whether a candidate should change user-level `AGENTS.md`, a repository `AGENTS.md`, a rules file, memory, or a skill.

### Can Add To User-Level AGENTS.md

Add information to user-level `AGENTS.md` only when all of these are true:

- It is a stable cross-project constraint that should affect most future Codex work before tools or memory are available.
- It changes concrete behavior: a trigger, a priority rule, a safety boundary, a routing decision, or a verification/reporting expectation.
- It is short enough to remain always-on without making simple tasks heavier.
- It is not better owned by a repository `AGENTS.md`, a skill, hook, MCP config, memory, CI/lint/test, or a task-specific prompt.
- It is written as an operational rule, not as background explanation, theory, raw research, or a task log.

Good user-level `AGENTS.md` examples:

- Skill-name-only requests must not imply unrelated side effects.
- Requirement files should produce adjacent `.plan.md` and `.task.md` unless the user narrows output.
- Complex configuration governance should investigate real context, identify the main blocker, and verify changes.
- Secrets must be redacted from outputs.

### Should Not Add To User-Level AGENTS.md

Do not add these to user-level `AGENTS.md`:

- One-off task history, progress logs, command transcripts, or temporary implementation details.
- Raw research notes, long explanations, political/philosophical theory text, or source excerpts.
- Secrets, credential values, auth file contents, cookies, private keys, or sensitive command output.
- Project-specific commands, architecture, dependency quirks, or module maps that belong in a repository or subdirectory `AGENTS.md` or `docs/总结`.
- Detailed workflows already owned by a skill, such as Feishu/Lark operations, research pipelines, GSD workflows, frontend design rules, or skill installation details.
- Preferences that are useful but not mandatory for all future tasks; store those in memory instead.
- Rules that duplicate stronger developer/system instructions, CI, hooks, tests, or existing AGENTS sections.
- Broad values like "be careful" unless translated into a concrete action and trigger.

### Where To Put Information Instead

| Information type | Preferred target |
| --- | --- |
| Stable user preference or decision | `agentMemory` / MCP memory |
| Workflow-specific procedure | Existing skill or new skill |
| Project command, architecture, dependency, or test workflow | Nearest repository/subdirectory `AGENTS.md` or `docs/总结` |
| Mandatory enforcement | Hook, CI, lint, test, or settings |
| Human-readable session narrative | Obsidian or task report |
| Interesting but unproven idea | Reviewable learning candidate or no action |
| Sensitive credential handling policy | Short AGENTS safety rule plus config comments; never raw values |

### How To Add To AGENTS.md

When an `AGENTS.md` update is justified:

1. Inspect the current file first and identify the smallest matching section.
2. Add or revise the minimum number of bullets; avoid new sections unless the concept has no clear home.
3. Use imperative, testable language with a clear trigger: "When X, do Y."
4. Preserve existing high-value local facts; compress rather than delete unless the replacement clearly covers them.
5. Avoid examples that contain secrets, internal URLs with credentials, raw command dumps, or long source text.
6. State routing boundaries: what belongs in AGENTS, what belongs in skills, hooks, MCP, memory, or repo docs.
7. Validate with a contradiction and criticism review: expected value, negative impact, duplication, and narrowest safe target.
8. After editing, verify the expected keywords/sections exist and report whether real config, hooks, MCP, or credentials were changed.

### AGENTS.md Decision Template

```text
Candidate: <rule or information>
Can add? <yes/no>
Target: <user AGENTS.md | repo AGENTS.md | rules | memory | skill | hook/CI | no action>
Why this target: <one sentence>
Upside: <future behavior improved>
Downside: <context bloat/conflict/privacy/maintenance risk>
Narrow wording: <proposed bullet if AGENTS.md>
Validation: <how to confirm the update did not overreach>
```

## Decision Rules

Do not make every retrospective item permanent. Persist only lessons that are likely to recur and are specific enough to improve future behavior.

Prefer memory over `AGENTS.md` for preferences and facts. Prefer skill edits over `AGENTS.md` for workflow-specific behavior. Prefer `AGENTS.md` only for high-confidence global constraints.

Prefer `no action` when an idea is interesting but not yet operational. Prefer `memory` when the lesson is durable but should not increase always-on prompt weight. Prefer `rules` or `AGENTS.md` only when future agents must obey it before tools or memory are available.

When evaluating a proposed update, explicitly account for both upside and downside. A high-value update can still be rejected if it creates broad ambiguity, conflicts with higher-priority instructions, stores sensitive information, or makes simple tasks heavier.

When a user merely names a skill, load and explain or apply that skill only to the current request. Do not infer permission to perform unrelated side effects.

Before changing hooks, confirm the requested behavior is actually hook-related. `codex-hooks` is for Codex hook configuration, not general summarization. Treat `skill-hook` as a legacy name only.

Use MCP and Obsidian deliberately. Prefer MCP memory for compact machine-readable rules that should influence future agents. Prefer Obsidian for narrative retrospectives, linked knowledge, daily notes, and material the user may read or edit manually. Ask for the target vault/path before writing Obsidian content when it cannot be inferred safely.

## Safety

Do not store secrets, tokens, private key contents, raw auth files, or sensitive command output. Redact fields matching token, secret, password, authorization, credential, key, or auth.

Do not rewrite large global instruction files for narrow lessons. Append or modify the smallest relevant section.

Do not overwrite existing user changes. Inspect target files before editing and preserve unrelated content.

## Output Shape

When finished, provide:

- `Persisted`: memories, skills, hooks, AGENTS.md, or files changed.
- `Not persisted`: candidates skipped and why.
- `Decision analysis`: principal contradiction, upside, downside, and chosen target for important candidates.
- `Validation`: commands or checks run.
- `Next trigger`: the exact phrase the user can use next time.

## References

Read `references/session-retrospective-checklist.md` when doing a non-trivial retrospective or when deciding where a lesson should be persisted.

Read `references/self-improvement-memory-model.md` when deciding whether a lesson is semantic memory, episodic evidence, or only working context.

Read `references/evolution-markers.md` before editing skills or long-lived rules based on session experience.
