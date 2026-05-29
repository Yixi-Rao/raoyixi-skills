# Self-Improvement Memory Model

Use this model when a session lesson may become durable context. It separates what should be generalized from what should stay as evidence or working context.

## Semantic Memory

Reusable patterns, rules, decisions, or anti-patterns.

Persist only when:

- The lesson is backed by repeated evidence, explicit user correction, or a verified recurring workflow.
- It changes a future behavior in a concrete way.
- It is safe to generalize beyond the current task.

Typical targets:

- `agentMemory` MCP memory for compact facts or decisions.
- Existing skill references for workflow-specific procedures.
- User-level `AGENTS.md` only for short, cross-project, always-on constraints.

## Episodic Memory

Specific experiences that justify or explain a future update.

Persist only when:

- The episode documents why a rule changed.
- It helps debug a repeated failure mode.
- It can be stored without secrets, raw credentials, private keys, or sensitive payloads.

Typical targets:

- Task completion files.
- Obsidian or human-readable retrospectives when requested.
- Reviewable learning candidates rather than hard rules.

## Working Memory

Current-session context that is useful now but should normally expire.

Do not persist when:

- The information is a transient command result, temporary file path, one-off task state, or unverified hypothesis.
- The value depends on this exact conversation only.
- The content contains secrets or raw auth data.

## Classification Template

```text
Candidate:
Evidence:
Memory type: semantic | episodic | working
Target: AGENTS.md | skill | memory | hook | repo docs | task file | no action
Positive value:
Negative impact:
Decision:
```
