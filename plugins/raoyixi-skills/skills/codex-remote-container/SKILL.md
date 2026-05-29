---
name: codex-remote-container
description: Configure and operate Codex inside a remote Docker/devcontainer reached via Docker Remote API, especially container250. Use when a user asks to connect Codex to a VS Code Remote Container, run interactive Codex in a remote container, sync Codex auth/config/skills, execute remote commands with docker -H, or run/evaluate tasks inside container250.
---

# Codex Remote Container

Use this skill for remote Docker/devcontainer setups where SSH is not the real control path and VS Code connects by Docker Remote API.

## Operating Model

Default container250 values:

```text
Docker Host: tcp://10.134.43.250:2376
Container: 0fd6ab612053
Remote CODEX_HOME: /data/jenkins/.codex/home
Remote Codex wrapper: /data/jenkins/.codex/bin/codex
Default workdir: /data/jenkins
```

Prefer this split:

- `c250:codex`: convenience entry that starts, sends to, or attaches to a named `c250-session`.
- `c250-session`: persistent remote Codex sessions backed by container-side `tmux`.
- `c250-codex`: interactive remote Codex TUI in the container.
- `c250-exec`: local-controller remote shell execution.
- `c250-sync-codex`: explicit auth/config/skill synchronization.
- Project `AGENTS.md`: store project rules in the remote repository, not in personal config.

Do not print `auth.json` contents or private tokens.

## Workflow

1. Confirm Docker API connectivity:
   ```bash
   docker -H tcp://10.134.43.250:2376 version
   docker -H tcp://10.134.43.250:2376 ps --format '{{.ID}} {{.Names}} {{.Status}}'
   ```
2. Inspect target container:
   ```bash
   docker -H tcp://10.134.43.250:2376 inspect --type container 0fd6ab612053 \
     --format '{{.Id}} {{.Name}} {{.State.Status}} {{.Config.User}} {{.Config.WorkingDir}}'
   ```
3. Use `c250-exec` for remote shell checks:
   ```bash
   c250-exec 'hostname; whoami; pwd'
   c250-exec -C /path/in/container 'ls -la'
   ```
4. Use `c250-session` for sustained multi-turn interaction where the remote Codex state must survive across local commands:
   ```bash
   c250:codex eval052001 -C /home/chehejia/cov-evalution "initial task"
   c250:codex eval052001 "follow-up message"
   c250:codex eval052001

   c250-session start eval052001 -C /home/chehejia/cov-evalution "initial task"
   c250-session send eval052001 "follow-up message"
   c250-session tail eval052001 -n 160
   c250-session attach eval052001
   c250-session stop eval052001
   ```
   This keeps the actual state in a remote `tmux` session running Codex inside the container. Use this for tasks that need 10+ follow-up messages.
5. Use `c250-codex` for direct one-off human/agent interaction:
   ```bash
   c250-codex
   C250_WORKDIR=/path/in/container c250-codex "initial task"
   ```
6. Sync only needed Codex state:
   ```bash
   c250-sync-codex --auth
   c250-sync-codex --config
   c250-sync-codex --skills codex-remote-container,codex-ssh-remote-onboarding
   ```
   Avoid default syncing every MCP/plugin because many depend on local-only paths, credentials, browsers, or macOS tools.
7. Validate remote Codex:
   ```bash
   c250-exec 'CODEX_HOME=/data/jenkins/.codex/home /data/jenkins/.codex/bin/codex login status'
   c250-exec 'CODEX_HOME=/data/jenkins/.codex/home /data/jenkins/.codex/bin/codex exec --skip-git-repo-check -C /data/jenkins "Run pwd using shell and answer with the path only."'
   ```

## Failure Handling

- Docker API `operation not permitted`: rerun with approval/escalation.
- Docker API `EOF` while direct `docker -H tcp://10.134.43.250:2376 ...` fails: check local proxy variables. If `ALL_PROXY` is set, ensure `NO_PROXY` includes `10.134.43.250,10.0.0.0/8,localhost,127.0.0.1,::1`. The `c250-*` wrappers set this automatically.
- Container Node too old: use the native Codex binary bundled in `@openai/codex-linux-x64` and keep `/data/jenkins/.codex/bin/codex` as wrapper.
- Local skills missing remotely: run `c250-sync-codex --skills ...`.
- Project rules ignored: start Codex with `C250_WORKDIR=/project/root` and ensure `AGENTS.md` exists under that tree.
- Multi-model eval script fails after first model: check whether sourced scripts polluted variables such as `SCRIPT_DIR`; use stable names like `BATCH_SCRIPT_DIR`.

## Record Keeping

For requirement-file-driven work:

- Keep `需求文件.md` unchanged as the source of truth.
- Put research in `需求文件.research.md`.
- Put implementation/evaluation logs in `需求文件.task.md`.
