---
name: self-improving-agent
description: Compatibility alias for the older self-improvement workflow. Use this when the user explicitly says $self-improving-agent, self-improve, 自我进化, 复盘经验, or asks to learn from a session; immediately route the work through $session-self-improvement.
---

# Self-Improving Agent

This skill is retained for backwards compatibility. The active implementation has been merged into `session-self-improvement`.

## Routing

When invoked, use `$HOME/.codex/skills/session-self-improvement/SKILL.md` as the authoritative workflow.

Preserve these concepts from the old workflow by loading the matching references only when needed:

- Multi-memory classification: `$HOME/.codex/skills/session-self-improvement/references/self-improvement-memory-model.md`
- Evolution and correction markers: `$HOME/.codex/skills/session-self-improvement/references/evolution-markers.md`
- Retrospective checklist: `$HOME/.codex/skills/session-self-improvement/references/session-retrospective-checklist.md`

## Guardrails

Do not auto-edit skills, memories, hooks, or AGENTS.md just because this alias was invoked. Apply the `session-self-improvement` necessity gate first, including expected value, negative impact, duplication, privacy risk, and the narrowest safe target.

The historical Claude-style hook metadata from this skill is intentionally not active in Codex. Use `codex-hook` for hook lifecycle work.

## Self-Improvement Process

### Phase 1: Experience Extraction

After any skill completes, extract:

```yaml
What happened:
  skill_used: {which skill}
  task: {what was being done}
  outcome: {success|partial|failure}

Key Insights:
  what_went_well: [what worked]
  what_went_wrong: [what didn't work]
  root_cause: {underlying issue if applicable}

User Feedback:
  rating: {1-10 if provided}
  comments: {specific feedback}
```

### Phase 2: Pattern Abstraction

Convert experiences to reusable patterns:

| Concrete Experience | Abstract Pattern | Target Skill |
|--------------------|------------------|--------------|
| "User forgot to save PRD notes" | "Always persist thinking to files" | prd-planner |
| "Code review missed SQL injection" | "Add security checklist item" | code-reviewer |
| "Callback was empty, didn't work" | "Verify callback implementations" | debugger |
| "Net APY position ambiguous" | "UI specs need exact relative positions" | prd-planner |

**Abstraction Rules:**

```yaml
If experience_repeats 3+ times:
  pattern_level: critical
  action: Add to skill's "Critical Mistakes" section

If solution_was_effective:
  pattern_level: best_practice
  action: Add to skill's "Best Practices" section

If user_rating >= 7:
  pattern_level: strength
  action: Reinforce this approach

If user_rating <= 4:
  pattern_level: weakness
  action: Add to "What to Avoid" section
```

### Phase 3: Skill Updates

Update the appropriate skill files with **evolution markers**:

```markdown
<!-- Evolution: 2025-01-12 | source: ep-2025-01-12-001 | skill: debugger -->

## Pattern Added (2025-01-12)

**Pattern**: Always verify callbacks are not empty functions

**Source**: Episode ep-2025-01-12-001

**Confidence**: 0.95

### Updated Checklist
- [ ] Verify all callbacks have implementations
- [ ] Test callback execution paths
```

**Correction Markers** (when fixing wrong guidance):

```markdown
<!-- Correction: 2025-01-12 | was: "Use callback chain" | reason: caused stale refresh -->

## Corrected Guidance

Use direct state monitoring instead of callback chains:
```typescript
// ✅ Do: Direct state monitoring
const prevPendingCount = usePrevious(pendingCount);
```
```

### Phase 4: Memory Consolidation

Use `$session-self-improvement` to decide whether any memory update is justified. Do not write local `memory/` files from this compatibility alias.

## Self-Correction (on_error hook)

Triggered when:
- Bash command returns non-zero exit code
- Tests fail after following skill guidance
- User reports the guidance produced incorrect results

**Process:**

```markdown
## Self-Correction Workflow

1. Detect Error
   - Capture error context from working/last_error.json
   - Identify which skill guidance was followed

2. Verify Root Cause
   - Was the skill guidance incorrect?
   - Was the guidance misinterpreted?
   - Was the guidance incomplete?

3. Apply Correction
   - Update skill file with corrected guidance
   - Add correction marker with reason
   - Update related patterns in semantic memory

4. Validate Fix
   - Test the corrected guidance
   - Ask user to verify
```

**Example:**

```markdown
<!-- Correction: 2025-01-12 | was: "useMemo for claimable ids" | reason: stale data at click time -->

## Self-Correction: Click-Time Computation

**Issue**: Using useMemo for claimable IDs caused stale data
**Fix**: Compute at click time for always-fresh data
**Pattern**: click_time_vs_open_time_computation
```

## Self-Validation

Use the validation template in `references/appendix.md` when reviewing updates.

## Hooks Integration

Do not install the historical Claude Code hook snippets directly. For Codex hook automation, route through `$codex-hook` and adapt the old hook scripts to `$HOME/.codex/hooks.json` only after the user explicitly asks for hook wiring.

## Additional References

See `references/appendix.md` for memory structure, workflow diagrams, metrics, feedback templates, and research links.

## Best Practices

### DO

- ✅ Learn from EVERY skill interaction
- ✅ Extract patterns at the right abstraction level
- ✅ Update multiple related skills
- ✅ Track confidence and apply counts
- ✅ Ask for user feedback on improvements
- ✅ Use evolution/correction markers for traceability
- ✅ Validate guidance before applying broadly

### DON'T

- ❌ Over-generalize from single experiences
- ❌ Update skills without confidence tracking
- ❌ Ignore negative feedback
- ❌ Make changes that break existing functionality
- ❌ Create contradictory patterns
- ❌ Update skills without understanding context

## Quick Start

After any skill completes, this agent automatically:

1. **Analyzes** what happened
2. **Extracts** patterns and insights
3. **Updates** relevant skill files
4. **Logs** to memory for future reference
5. **Reports** summary to user

## References

- [SimpleMem: Efficient Lifelong Memory for LLM Agents](https://arxiv.org/html/2601.02553v1)
- [A Survey on the Memory Mechanism of Large Language Model Agents](https://dl.acm.org/doi/10.1145/3748302)
- [Lifelong Learning of LLM based Agents](https://arxiv.org/html/2501.07278v1)
- [Evo-Memory: DeepMind's Benchmark](https://shothota.medium.com/evo-memory-deepminds-new-benchmark)
- [Let's Build a Self-Improving AI Agent](https://medium.com/@nomannayeem/lets-build-a-self-improving-ai-agent-that-learns-from-your-feedback-722d2ce9c2d9)
