# Codex Adaptation

This skill is installed for Codex, but its upstream automatic observation system is written for Claude Code plugin hooks.

## Current Codex Status

- Skill discovery works from `$HOME/.codex/skills/continuous-learning-v2`.
- Claude-specific `~/.claude/settings.json` hook snippets should not be copied into Codex.
- Codex hooks are wired through `$HOME/.codex/hooks.json`.
- The dispatcher is `$HOME/.codex/hooks/codex_learning_hook.py`.
- Events are mirrored into the v2 homunculus project observations file.
- Learning outputs are reviewable candidates first, not automatic skill edits.

## Manual Commands

Run from any project directory:

```bash
python3 $HOME/.codex/skills/continuous-learning-v2/scripts/instinct-cli.py status
python3 $HOME/.codex/skills/continuous-learning-v2/scripts/instinct-cli.py projects
python3 $HOME/.codex/skills/continuous-learning-v2/scripts/instinct-cli.py evolve
python3 $HOME/.codex/hooks/learning_review.py list
```

Data is stored under:

```text
${XDG_DATA_HOME:-$HOME/.local/share}/ecc-homunculus
```

## Practical Codex Use

Use this skill when the user asks for:

- "持续学习"
- "总结经验"
- "沉淀成规则"
- "把这个模式记下来"
- "把经验进化成 skill/command"

For persistent project facts, prefer the `agentMemory` MCP tools. For pattern review and evolution, use this skill's CLI and review candidates with `learning_review.py`.

## Review and Promotion

The hook creates candidates in `$HOME/.codex/learning/candidates.jsonl`.

Use:

```bash
python3 $HOME/.codex/hooks/learning_review.py list
python3 $HOME/.codex/hooks/learning_review.py export-eval <candidate-id>
python3 $HOME/.codex/hooks/learning_review.py promote <candidate-id> --title "Short reusable rule"
```

Promoted memories are stored in `$HOME/.codex/learning/approved-memories.jsonl` and are injected on later `SessionStart` hooks as additional local learning context.
