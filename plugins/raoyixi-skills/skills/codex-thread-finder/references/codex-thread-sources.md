# Codex Thread Sources

## Local Sources

Use `${CODEX_HOME:-$HOME/.codex}` as the local root.

Important files:

- `.codex-global-state.json`: UI state, Remote SSH connection metadata, thread-to-project assignments, prompt history, workspace hints.
- `state_5.sqlite`: `threads` table with `id`, `rollout_path`, `created_at`, `updated_at`, `cwd`, `title`, and related metadata.
- `session_index.jsonl`: fallback title/update index.
- `sessions/**/rollout-*.jsonl`: authoritative per-event conversation log when available.

## Top-Level State Keys

The Remote SSH keys are top-level keys in `.codex-global-state.json`, not children of `electron-persisted-atom-state`.

- `thread-project-assignments`: maps thread ID to project ID.
- `remote-projects`: maps project ID to `hostId` and `remotePath`.
- `codex-managed-remote-connections`: maps `hostId` to SSH alias/display metadata.
- `electron-persisted-atom-state.prompt-history`: may contain `thread_id -> prompts[]` even when local SQLite has no thread row.

## Remote SSH Search

For every configured SSH alias:

1. Run a short read-only SSH probe with `BatchMode=yes` and `ConnectTimeout`.
2. Discover real remote Codex homes:
   - read live `/proc/<pid>/environ` for `CODEX_HOME`
   - test `/lpai/.codex-*-home`
   - test `/lpai/*/.codex/home`
   - test `~/.codex`
   - test `/root/.codex`
3. In every discovered home, scan `state_5.sqlite`, `session_index.jsonl`, and `sessions/**/rollout-*.jsonl`.

Do not assume the Remote SSH session store is under `~/.codex`.

## Ranking

Primary rank: number of user messages inside the requested time range.

Tie breakers:

1. total event count observed in the same thread
2. latest user message timestamp
3. thread ID lexical order for deterministic output

## Deep Links

Return `codex://thread/<thread_id>` as a best-effort local Codex thread deep link. If a future stable URL scheme is available in Codex state, prefer the verified scheme and mention the source.

## Optional Content Export

Conversation content export should be opt-in. Use it only when the user asks to download, save, export, include, or show the selected conversation.

Supported script options:

- `--limit N`: return the top N ranked threads; JSON output includes `top_candidates`.
- `--include-content`: include selected thread messages in stdout or JSON output.
- `--content-output <path>`: save selected thread messages as Markdown and report the path.
- `--content-output-dir <path>`: save each ranked thread message export as `NN-<thread_id>.md`.
- `--content-scope range`: export only user/assistant messages whose event timestamps are inside the requested time range.
- `--content-scope full`: export all user/assistant messages in the selected thread.
- `--max-message-chars N`: truncate each exported message; `0` disables per-message truncation.

Exported content should come from each selected ranked thread's session JSONL path. For Remote SSH winners, retrieve content from the remote host over SSH using the candidate's `remote_alias` and `rollout_path`.

Only export `user` and `assistant` message bodies. Do not export system or developer instructions, raw tool payloads, credentials, or auth files. Redact obvious token/password/secret-style key-value strings before output.
