---
name: codex-thread-finder
description: Find the most active Codex conversation in a user-specified time range across local Codex Desktop sessions and connected Remote SSH Codex homes. Use when the user asks to locate, rank, audit, or report the highest-frequency Codex thread/conversation and return its source, title, thread ID, deep link, working directory, Remote SSH health/search diagnostics, and optionally export or include the selected thread's conversation content.
---

# Codex Thread Finder

## Overview

Use this skill to find the Codex thread with the highest user interaction count in a time range. The important part is Remote SSH coverage: if the local Codex state shows connected Remote SSH hosts, probe them and scan their real `CODEX_HOME` session stores instead of falling back to local-only evidence.

## Quick Start

Run the bundled script with an explicit start and end time:

```bash
python3 <skill-dir>/scripts/find_codex_thread.py \
  --start "2026-06-15 00:00" \
  --end "2026-06-15 23:59:59"
```

For automation, top-N ranking, or downstream parsing, add `--limit` and `--json`.

```bash
python3 <skill-dir>/scripts/find_codex_thread.py \
  --start "2026-06-15 00:00" \
  --end "2026-06-15 23:59:59" \
  --limit 3 \
  --json
```

If the user asks to download, export, include, or show the conversation content, request it explicitly:

```bash
python3 <skill-dir>/scripts/find_codex_thread.py \
  --start "2026-06-15 00:00" \
  --end "2026-06-15 23:59:59" \
  --limit 3 \
  --include-content \
  --content-output-dir "/tmp/codex-threads"
```

Resolve `<skill-dir>` to the directory containing this `SKILL.md`.

## Required Behavior

1. Interpret the requested time range before scanning.
2. Scan local Codex sources under `${CODEX_HOME:-$HOME/.codex}`.
3. Read top-level `.codex-global-state.json` fields:
   - `thread-project-assignments`
   - `remote-projects`
   - `codex-managed-remote-connections`
   - `electron-persisted-atom-state.prompt-history`
4. If Remote SSH connections exist, probe every alias with SSH and scan healthy hosts.
5. On each healthy Remote SSH host, discover the real `CODEX_HOME`; do not assume `~/.codex`.
6. Rank by user message count inside the requested time range. Break ties by total event count, then most recent user message time.
7. Return the requested number of ranked threads with `--limit N`; keep `best` as the top-ranked thread for backward compatibility.
8. Return each ranked thread with:
   - `source`: `local` or `remote-ssh`
   - Remote SSH alias/host when applicable
   - title
   - thread ID
   - deep link
   - working directory
   - session JSONL path when known
   - count/evidence details
   - Remote SSH diagnostics
9. Do not include full conversation content by default. Include or save selected-thread content only when the user asks for it.

## Remote SSH Rules

If there are no Remote SSH connections in local Codex state, say so.

If a Remote SSH alias is configured but unreachable, report that alias and the error. Do not present a local thread as a complete global result without saying Remote SSH coverage was incomplete.

If SSH is healthy, scan the remote host. The script must inspect process environments and common Codex homes such as:

- `CODEX_HOME` from live Codex/app-server processes
- `/lpai/.codex-*-home`
- `/lpai/*/.codex/home`
- `~/.codex`
- `/root/.codex`

If a high-frequency thread appears only in local `prompt-history` and is assigned to a Remote SSH project, treat it as a high-confidence remote candidate that needs remote session verification. If the remote session JSONL cannot be found, report the limitation explicitly rather than silently downgrading to a lower-ranked local thread.

## Evidence Notes

Prefer precise evidence from SQLite `threads` metadata plus rollout/session JSONL message timestamps. Use `prompt-history` as fallback evidence only because it may not contain per-message timestamps.

Use `references/codex-thread-sources.md` if you need to explain or patch the source discovery logic.

## Optional Conversation Content

Use `--include-content` when the user asks to show the conversation content inline. Use `--content-output <path>` when saving only the top-ranked conversation. Use `--content-output-dir <dir>` with `--limit N` when the user asks to download, save, or export multiple ranked conversations.

Content export reads only ranked thread user and assistant messages from the session JSONL. It excludes system/developer instructions and tool payloads. The script redacts obvious token/password/secret-style key-value strings and truncates each message at `--max-message-chars` characters by default.

Use `--content-scope range` by default so the exported messages match the requested time window. Use `--content-scope full` only when the user asks for the full selected thread.

## Output Shape

When answering the user, keep the result compact:

```text
Top 3 active threads:
- Source: remote-ssh (llm_eval)
- Title: ...
- Thread ID: ...
- Deep link: codex://thread/...
- Working directory: /lpai/...
- User messages in range: ...
- Evidence: ...
- Remote SSH diagnostics: ...
- Conversation content: saved to ...
```

If evidence is incomplete, say exactly which layer failed: no configured Remote SSH connection, SSH alias unreachable, remote `CODEX_HOME` not found, session JSONL missing, SQLite unreadable, or prompt-history lacks timestamps.
