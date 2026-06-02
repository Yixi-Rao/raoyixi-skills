---
name: vscode-renderer-crash-debug
description: "Diagnose and repair VS Code macOS renderer crash loops, especially Remote-SSH windows showing The window terminated unexpectedly or CodeWindow renderer process gone reason crashed code 5. Use when Codex must inspect VS Code logs, Crashpad dumps, Remote-SSH resolution, extension activation errors, GitHub Copilot Chat, CopilotCLI, Claude Agent failures, or safely isolate bad VS Code extensions without losing unsaved work."
---

# VS Code Renderer Crash Debug

## Overview

Use this skill to debug VS Code window crashes from evidence, not guesses. Treat `renderer process gone (reason: crashed, code: 5)` as a local VS Code Electron renderer failure until logs prove otherwise, even when the visible workspace is Remote-SSH.

## First Response

1. Preserve user work.
   - Do not force quit VS Code while unsaved tabs may exist.
   - If a crash dialog is visible, inspect logs before clicking `Reopen` unless a repair step is already prepared.
2. Collect evidence before fixing.
   - Run `scripts/collect_vscode_crash_evidence.py`.
   - Use `--since "YYYY-MM-DD HH:MM:SS"` when the user reports a fresh recurrence.
3. Separate facts from suspects.
   - Hard fact: `main.log` plus Crashpad dump proves the crashed process.
   - Suspect: an extension error near the crash.
   - Root candidate: a suspect that remains on the latest crash path and disappears after isolation.

## Evidence Workflow

Run:

```bash
python3 <skill-dir>/scripts/collect_vscode_crash_evidence.py --since "YYYY-MM-DD HH:MM:SS"
```

Resolve `<skill-dir>` to the directory containing this `SKILL.md`.

Read the output in this order:

1. `main.log` tail.
   - Confirm `CodeWindow: renderer process gone (reason: crashed, code: 5)`.
2. Crashpad dump strings.
   - Confirm `Code Helper (Renderer)`, `Electron Framework`, `--type=renderer`.
3. Window logs newer than the last fix.
   - Focus on the newest `windowN`, not stale earlier windows.
4. Extension host logs.
   - If they say `renderer closed the MessagePort`, the extension host died after the renderer, not before.
5. Remote-SSH logs.
   - If `resolveAuthority(ssh-remote)` returns `WebSocket(127.0.0.1:PORT)`, the Remote-SSH connection path resolved; do not blame SSH alone.

## Known Crash Chain

Read `references/case-study-2026-06-02.md` when logs contain any of:

- `GitHub.copilot-chat`
- `CopilotCLI`
- `chatParticipant must be declared in package.json`
- `copilot-cloud-agent`
- `copilotcli`
- `claude-code`
- `Anthropic.claude-code`

In the 2026-06-02 case, the root chain was:

`GitHub.copilot-chat` activates -> CopilotCLI/Claude chat session integration starts -> chat participants are not correctly declared or registered -> local Electron renderer crashes.

Do not describe this as a user code problem or PUA skill problem unless new evidence proves that. It was a VS Code built-in Copilot Chat/runtime state issue.

## Repair Ladder

Apply only the smallest step supported by current evidence.

1. Remove proven-bad user extensions.
   - Move the extension directory out of `~/.vscode/extensions`.
   - Remove its id from `~/.vscode/extensions/extensions.json`.
   - Back up `extensions.json` first.
2. For duplicate icon command conflicts:
   - Isolate `lqyld.vscode-icons-iconify` first if logs show `vscode-icons.activateIcons already registered`.
3. For old selection-highlight event failures:
   - Isolate `cliffordfajardo.hightlight-selections-vscode` if logs show repeated `FAILED to handle event`.
4. For Copilot Chat participant failures:
   - First try disabling specific settings if the crash has not recurred after that level.
   - If the crash recurs and `GitHub.copilot-chat` still activates, setting-only suppression is insufficient.
   - Persistently disable `github.copilot-chat` and `github.copilot` in `User/globalStorage/state.vscdb`.
   - Move the built-in Copilot extension directory out of the VS Code app bundle only when the evidence remains on that path.
   - Move `anthropic.claude-code` out of user extensions when `claude-code` participant errors are present.
5. Reopen VS Code and verify.
   - No new Crashpad dump after the fix time.
   - No new `renderer process gone` in `main.log`.
   - Newest `windowN` lacks the previously implicated activation and error chain.

## Failed Fixes To Remember

Do not stop at a fix merely because the immediate window reopens. In the known case these were insufficient alone:

- Isolating only `lqyld.vscode-icons-iconify`.
- Isolating only `cliffordfajardo.hightlight-selections-vscode`.
- Adding only Copilot subfeature settings such as `github.copilot.chat.backgroundAgent.enabled: false` and `github.copilot.chat.cli.mcp.enabled: false`.

Those changes removed real noise but did not stop later crashes while `GitHub.copilot-chat` still activated.

## Reporting Standard

Report with:

- Latest crash time and dump path.
- Exact `main.log` line proving renderer crash.
- Whether Remote-SSH resolved successfully.
- Newest `windowN` path and the crash-adjacent extension chain.
- What was changed, where backups were written, and how to roll back.
- Confidence level and residual risk.

Redact tokens, auth headers, private keys, cookies, and API keys in all summaries.
