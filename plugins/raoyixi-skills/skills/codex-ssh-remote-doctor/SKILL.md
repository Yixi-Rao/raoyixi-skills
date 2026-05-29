---
name: codex-ssh-remote-doctor
description: Diagnose, repair, or validate existing Codex SSH remote connections for LPAI or similar SSH hosts. Use when a user asks to fix remote login/auth, repair RemoteForward proxy access to OpenAI/ChatGPT, restore a remote codex wrapper, copy local Codex auth to a trusted remote, set approval/sandbox defaults, or debug errors such as Not logged in, remote port forwarding failed, bwrap sandbox failure, missing codex/node/npm, or stream disconnected.
---

# Codex SSH Remote Doctor

## Core Workflow

Use the source SSH alias and remote workspace the user provides. If the user uses a near miss such as `llm-eval` when only `llm_eval` exists, inspect both with `ssh -G` and either update the existing alias or add an alias synonym.

1. Inspect local SSH config and connectivity:
   - `ssh -G {alias} | grep -E '^(hostname|port|user|identityfile|remoteforward|exitonforwardfailure) '`
   - `ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes {alias} 'hostname; whoami; pwd'`
2. Ensure local proxy is available before using RemoteForward:
   - Check likely ports such as `127.0.0.1:7897`.
   - Add or repair `RemoteForward 127.0.0.1:18080 127.0.0.1:{local_proxy_port}`.
   - Prefer `ExitOnForwardFailure no` for App/VS Code coexistence, because multiple SSH sessions may race for the same remote port.
3. Identify the remote workspace:
   - Prefer the actual repo with `.git`, for example `/lpai/code/verl-0407` or `/lpai/llm-eval`.
   - Do not hardcode `/lpai/code/rllm`; it is only an example.
4. Restore remote Codex:
   - Use project-local paths: `{workdir}/.codex/cli` and `{workdir}/.codex/home`.
   - If the workspace path is long, do not use `{workdir}/.codex/home` as `CODEX_HOME` for Codex App. Use a short path such as `/lpai/.codex-{alias}-home` to avoid Unix socket `SUN_LEN` failures.
   - If npm exists, install with `npm install -g --prefix {workdir}/.codex/cli @openai/codex`.
   - If npm is absent but a compatible Linux x64 CLI exists on another trusted remote, copy the project-local CLI tree.
   - Write `/usr/local/bin/codex` as a wrapper that sets `CODEX_HOME`, proxy env vars, and finds a bundled VS Code `node` if `node` is absent from PATH.
5. Configure auth and permissions:
   - Copy local `~/.codex/auth.json` to `{workdir}/.codex/home/auth.json` and `/root/.codex/auth.json`; never print file contents.
   - Set both files to mode `600`.
   - Write `config.toml` with `approval_policy = "never"`, `sandbox_mode = "danger-full-access"`, `features.network_proxy = true`, and trusted project entries.
6. Restart stale remote app-server/proxy processes and remove stale app-server control directories when needed.
7. Validate in this order:
   - `codex --version`
   - `codex login status`
   - proxy curl through `127.0.0.1:18080`
   - `codex doctor --summary`
   - `codex exec --skip-git-repo-check -C {workdir} "Run pwd using shell and answer with the path only."`

## Important Defaults

- Use `ClearAllForwardings=yes` for diagnostics that should not create or rely on SSH port forwarding.
- Do not use `ClearAllForwardings=yes` when validating the proxy path or ChatGPT/OpenAI reachability through the SSH tunnel.
- A warning like `remote port forwarding failed for listen port 18080` can be harmless when another live SSH/Codex connection already owns the remote forwarded port. Verify with proxy curl or `codex exec` before treating it as fatal.
- If `codex doctor` fails connectivity under `ClearAllForwardings=yes`, rerun without that option.
- Existing Codex App tasks may retain old approval settings. New sessions read the updated `config.toml`.
- `Error: path must be shorter than SUN_LEN` means the app-server Unix socket path is too long. Move `CODEX_HOME` to a short directory while keeping `-C {workdir}` pointed at the real repo.
- If HTTPS curl through the proxy works but `codex doctor` reports WebSocket failures or App shows reconnects, enable `[features] network_proxy = true`.

## Bundled Resources

- Read `references/workflow.md` when you need exact command templates, wrapper content, fallback installation patterns, or troubleshooting details.
- Run `scripts/diagnose_codex_ssh_remote.sh {alias} {workdir}` for a quick read-only status check before making changes.
