# Codex Adaptation

This skill is installed for Codex as a manual/self-review workflow.

## Current Codex Status

- Skill discovery works from `$HOME/.codex/skills/self-improving-agent`.
- The upstream Claude-style hook examples are not registered directly.
- Codex uses `$HOME/.codex/hooks.json` and `$HOME/.codex/hooks/codex_learning_hook.py`.
- The self-improvement loop is gated: observations create candidates, candidates can become evals or approved memories, and skill edits remain explicit.

## Practical Codex Use

Use this skill when the user asks for:

- "自我进化"
- "复盘这次经验"
- "把失败原因沉淀下来"
- "改进某个 skill"
- "从今天的操作里总结规则"

Persist durable lessons through the `agentMemory` MCP tools when they are reusable across sessions. Keep code or skill edits explicit and reviewable.

## High-Quality Loop

1. Observe Codex lifecycle events via hooks.
2. Scrub secrets before persisting.
3. Mirror observations into `continuous-learning-v2` project storage.
4. Generate reviewable failure, approval, and user-correction candidates.
5. Export selected candidates as eval tasks.
6. Promote only reviewed candidates into approved memories.
7. Update skills only after an eval or repeated evidence justifies the change.
