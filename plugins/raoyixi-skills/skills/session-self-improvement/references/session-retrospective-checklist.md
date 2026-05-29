# Session Retrospective Checklist

## Evidence Sources

- Current visible conversation.
- Compaction summary, if present.
- User corrections and explicit frustration.
- Tool outputs that prove a cause or fix.
- Files changed during the session.
- Existing skill and AGENTS.md instructions.

## Candidate Quality Bar

Persist a lesson when it is:

- Durable: likely to matter in future sessions.
- Actionable: changes a concrete behavior.
- Scoped: clear whether global, project-specific, or skill-specific.
- Evidence-backed: tied to user correction, repeated failure, or verified outcome.
- Safe: contains no secret or sensitive raw data.

Skip a lesson when it is:

- A one-off command result.
- A speculative cause without verification.
- Merely a task progress note.
- Already covered by a stronger existing rule.
- Too broad to guide behavior.

## Persistence Targets

Use `agentMemory` for stable facts, preferences, decisions, and recurring failure modes.

Use MCP memory for compact, durable, machine-readable rules. Good candidates include user preferences, repeated agent errors, project decisions, reusable debugging patterns, and skill behavior rules.

Use Obsidian when the user wants a readable knowledge base, linked notes, daily/session retrospectives, or material that should be browsed and edited manually. Ask for the vault and note path if they are not explicit.

Use `continuous-learning-v2` style instincts for small behavior rules:

```yaml
trigger: "when the user names a skill without a task"
action: "load or explain the skill; do not perform unrelated side effects"
evidence: "user correction during skill-hook confusion"
scope: global
```

Use `AGENTS.md` for hard global constraints that should apply regardless of skill.

Use an existing skill when the rule only affects that skill's trigger, workflow, or safety boundary.

Create a new skill when the workflow is repeated, multi-step, and not owned by an existing skill.

Use `codex-hooks` when the improvement requires Codex lifecycle automation. Do not use hook automation for general summaries unless the user explicitly asks for that automation.

## AGENTS.md Candidate Checklist

Before updating user-level `AGENTS.md`, confirm:

- [ ] The rule is stable across projects and should affect most future Codex work.
- [ ] The rule must be available before tools, skills, or memory are consulted.
- [ ] The rule is actionable and has a clear trigger.
- [ ] The rule is shorter than the workflow it replaces.
- [ ] The rule is not a task log, research note, raw command output, or background explanation.
- [ ] The rule is not better stored in memory, a skill, hook, MCP config, CI/lint/test, repo `AGENTS.md`, or `docs/总结`.
- [ ] The rule does not duplicate a stronger system/developer/user instruction.
- [ ] The rule introduces no secrets, credentials, or sensitive internal values.
- [ ] The expected benefit outweighs context bloat, conflict risk, stale-rule risk, and maintenance cost.

If any item fails, do not update user-level `AGENTS.md`; choose the narrower persistence target.

Preferred fallback targets:

- Memory for durable preferences, facts, and decisions.
- Existing skill for workflow-specific trigger rules or procedures.
- Repository `AGENTS.md` or `docs/总结` for project-specific commands, architecture, dependencies, and tests.
- Hook, CI, lint, test, or settings for mandatory enforcement.
- No action for interesting but unproven ideas.

## Reporting Template

```text
Persisted:
- memory: <key> - <why>
- skill: <path> - <what changed>

Not persisted:
- <candidate> - <reason>

Validation:
- <command/check>: <result>

Next trigger:
- Use session-self-improvement to review this session and persist durable lessons.
```
