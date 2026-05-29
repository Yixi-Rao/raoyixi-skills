---
name: codex-hook
description: Create, modify, validate, or troubleshoot Codex hook configuration and hook scripts, including SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, and Stop. Use when the user asks about Codex hooks, migrating old skill-hook behavior, automating lifecycle events, wiring session learning/self-improvement hooks, or debugging $HOME/.codex/hooks.json and $HOME/.codex/hooks/.
---

# Codex Hook

## Scope

Work on Codex hooks only. Codex hooks live at:

```text
$HOME/.codex/hooks.json
$HOME/.codex/hooks/
```

This skill replaces the old `skill-hook` name. When older notes mention `skill-hook`, interpret that as `codex-hook`.

## Workflow

1. Read `$HOME/.codex/hooks.json`.
2. Read only the relevant script under `$HOME/.codex/hooks/`.
3. Preserve existing hook entries and append or edit narrowly.
4. If the requested behavior fits an existing script, extend that script narrowly.
5. If the behavior is independent, add a small dedicated hook script.
6. Validate JSON syntax and run the hook script with representative stdin where practical.
7. Keep hooks non-blocking: hook failures should log and return success unless the user explicitly wants a blocking guard.

## Event Names

Use the exact event names already present in the local Codex config:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PermissionRequest`
- `PostToolUse`
- `Stop`

## Self-Improvement Hooks

When asked to automate session learning or self-improvement:

- Prefer reviewable candidate generation over automatic skill edits.
- Never store secrets from hook payloads.
- Redact keys matching token, secret, password, authorization, credential, key, or auth.
- Keep hook-triggered work lightweight; defer expensive analysis to explicit user requests or background-safe commands.
- Do not make a hook start SSH tunnels, edit skills, or write global constraints unless the user explicitly asks for that side effect.

## MCP And Knowledge Base Hooks

When hooks need to interact with MCP, Obsidian, or other knowledge stores:

- Use MCP tools only when they are available in the current session and the target write is durable and scoped.
- Prefer `agentMemory` for compact durable preferences, decisions, patterns, and bug lessons.
- Prefer Obsidian skills for human-readable notes, linked knowledge, daily logs, or vault-managed retrospectives.
- Do not duplicate the same lesson across memory, Obsidian, and AGENTS.md unless each target has a distinct purpose.
- If Obsidian requires a running app, vault selection, or write permission, ask the user for the exact vault/path and any needed manual action.

## Permission Boundary

If Codex cannot write under `$HOME/.codex/hooks` or `$HOME/.codex/hooks.json`, stop and ask for manual help. Provide exact commands instead of attempting unrelated workarounds.

Do not print private key contents, auth files, tokens, or hook payload secrets.

## Reference

Read `references/codex-hook-checklist.md` for validation and troubleshooting details.
