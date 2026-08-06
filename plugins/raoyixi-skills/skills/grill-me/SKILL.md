---
name: grill-me
description: "Pressure-test a plan, design, architecture, PRD, API, or data model through a one-question-at-a-time interview that resolves dependent decisions. Use when the user says 'grill me', asks for hard questions or a critical challenge of a proposal, or wants to clarify a design before implementation."
---

# Grill Me

Turn premature agreement into explicit, shared decisions. Be constructively demanding: expose assumptions, dependencies, failure modes, and trade-offs without becoming adversarial.

## Start

1. Read the supplied plan or design and inspect every referenced file, codebase area, and existing decision record that can answer a question.
2. Build a lightweight decision tree: identify the highest-impact unresolved decision, its prerequisites, and consequential branches.
3. Do not ask the user for information that can be discovered from the available artifacts. State relevant evidence when it changes the recommendation.
4. Do not implement, edit, or create durable planning artifacts during the interview unless the user explicitly asks for that work.

## Interview loop

Ask **exactly one** decision-making question per turn, then wait for the user's answer.

- Ask prerequisite decisions before their dependents.
- Work depth-first: close a branch before opening unrelated branches.
- Choose the question with the greatest downstream impact when several are ready.
- Provide a recommended answer every time, including a concise rationale grounded in codebase evidence or stated constraints.
- Challenge vague answers by turning them into a clear decision, success criterion, boundary, or trade-off.
- If the user delegates the choice, adopt the recommendation and label it as an assumption for confirmation.
- Keep a short internal record of locked decisions; do not repeat resolved questions.

Use this format:

```markdown
Q[n] — <one concrete question>

Recommended answer: <specific choice>.
Why: <one or two sentences, citing inspected evidence when available>.
Trade-off: <what this choice gives up or protects against>.
```

## What to test

Prioritize, in this order when relevant:

1. Goal, user, and measurable success condition.
2. Scope, non-goals, and rollout boundary.
3. Domain model, ownership, source of truth, and lifecycle.
4. Interfaces: API contracts, inputs/outputs, compatibility, and error behavior.
5. Dependencies, ordering, concurrency, idempotency, and failure recovery.
6. Security, privacy, permissions, cost, performance, observability, and testing.
7. Migration, rollback, and operational ownership.

Do not spend turns on naming, formatting, or implementation minutiae while a more consequential decision remains unresolved.

## Finish

When every material branch is resolved, say **“Shared understanding reached.”** Summarize:

- locked decisions and their rationale;
- explicit assumptions and remaining risks;
- non-goals and unresolved follow-ups;
- the recommended next artifact or action (for example, a PRD, issue breakdown, or implementation plan).

Only move into that next phase if the user requests it.

## Origin

This Codex-native version preserves the interview discipline of Matt Pocock's MIT-licensed \`grill-me\` skill while intentionally omitting Claude-specific command wrappers and external session scripts.
