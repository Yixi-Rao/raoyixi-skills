# Evolution Markers

Use these markers when editing a skill, rule, memory, or AGENTS.md based on session experience. They keep self-improvement reviewable and prevent automatic overreach.

## Marker Types

- `pattern-extraction`: a repeated workflow or behavior became reusable guidance.
- `correction`: prior guidance caused or allowed an error and needs narrowing.
- `governance`: routing, ownership, safety, or verification rules became clearer.
- `defer`: useful idea, but evidence is weak or side effects are not yet understood.
- `reject`: negative impact, duplication, privacy risk, or scope creep outweighs value.

## Required Review

Before writing a durable update:

1. State the candidate lesson.
2. Identify the evidence and whether it is repeated, user-confirmed, or inferred.
3. Name the principal contradiction: future usefulness vs context bloat, automation vs side effects, or global consistency vs local specificity.
4. Choose the narrowest target.
5. Record the expected upside and possible harm.
6. Validate the changed artifact.

## Skill Change Marker

```text
Evolution marker: pattern-extraction | correction | governance
Source evidence:
Changed target:
Why this target:
Rejected broader targets:
Validation:
```

## Correction Marker

```text
Issue:
Previous guidance:
Corrected guidance:
Root cause:
Follow-up validation:
```

## Guardrails

- Do not store secrets, raw auth files, private key contents, tokens, or unredacted request payloads.
- Do not promote a single anecdote into user-level AGENTS unless the user explicitly wants it as a global rule and it passes the necessity gate.
- Prefer a skill reference over always-on instructions when the workflow is specialized.
- Prefer reviewable candidates over automatic edits when confidence is low.
