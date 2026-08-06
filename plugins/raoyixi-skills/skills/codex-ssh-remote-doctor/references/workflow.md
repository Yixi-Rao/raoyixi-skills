# Codex SSH Remote Doctor Workflow

## Variables

Use task-specific values:

```text
SSH_ALIAS        SSH alias, e.g. llm_eval, llm-eval, verl_test
REMOTE_WORKDIR   Trusted remote repo, e.g. /lpai/llm-eval or /lpai/code/verl-0407
CODEX_CLI_DIR    ${REMOTE_WORKDIR}/.codex/cli
CODEX_HOME_DIR   ${REMOTE_WORKDIR}/.codex/home
LOCAL_PROXY      usually 127.0.0.1:7897 on this machine
REMOTE_PROXY     usually 127.0.0.1:18080 on the remote
```

If `REMOTE_WORKDIR` is long, set `CODEX_HOME_DIR` to a short path such as `/lpai/.codex-${SSH_ALIAS}-home`. Codex App uses Unix sockets under `CODEX_HOME`; long paths can fail with `Error: path must be shorter than SUN_LEN`.

## SSH Config

Inspect first:

```bash
ssh -G "$SSH_ALIAS" | grep -E '^(hostname|port|user|identityfile|remoteforward|exitonforwardfailure) '
ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$SSH_ALIAS" 'hostname; whoami; pwd'
```

Recommended alias block:

```sshconfig
Host SSH_ALIAS
  HostName ssh-d.lpai.lixiang.com
  Port PORT_FROM_LPAI
  User root
  StrictHostKeyChecking no
  RemoteForward 127.0.0.1:18080 127.0.0.1:7897
  ExitOnForwardFailure no
```

Use `ExitOnForwardFailure no` for daily use because Codex App, VS Code Remote SSH, and manual SSH can connect concurrently. If the first connection already owns `18080`, later connections may warn but still work through the already established tunnel.

## Remote Checks

```bash
ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$SSH_ALIAS" \
  'command -v node || true; node --version 2>/dev/null || true; command -v npm || true; npm --version 2>/dev/null || true; command -v codex || true; codex --version 2>/dev/null || true'

ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$SSH_ALIAS" \
  'find /lpai /home/jovyan -maxdepth 3 -type d \( -name .git -o -iname "*verl*" -o -iname "*eval*" -o -iname "*rllm*" \) 2>/dev/null | sed -n "1,120p"'
```

## Install or Restore Codex CLI

If remote has npm:

```bash
ssh "$SSH_ALIAS" "mkdir -p '$CODEX_CLI_DIR' '$CODEX_HOME_DIR' && npm install -g --prefix '$CODEX_CLI_DIR' @openai/codex && '$CODEX_CLI_DIR/bin/codex' --version"
```

If remote lacks npm but another compatible Linux x64 remote has a project-local CLI:

```bash
ssh SOURCE_ALIAS "tar -C '$SOURCE_WORKDIR/.codex' -czf - cli" \
  | ssh "$SSH_ALIAS" "mkdir -p '$REMOTE_WORKDIR/.codex' && tar -C '$REMOTE_WORKDIR/.codex' -xzf -"
```

This is useful for LPAI containers where VS Code provides `node` but not `npm`.

## Check or Upgrade CLI Version

Always show the currently effective CLI path and version before deciding that a remote is healthy:

```bash
ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$SSH_ALIAS" \
  'printf "%s\n" "---effective codex---"; command -v codex; readlink -f "$(command -v codex)" 2>/dev/null || true; codex --version; printf "%s\n" "---app-server---"; codex app-server daemon version 2>/dev/null || true; printf "%s\n" "---doctor updates---"; codex doctor --summary 2>/dev/null | sed -n "/Updates/,/Connectivity/p"'
```

If `codex doctor --summary` reports `updates ... available`, upgrade the active CLI before debugging higher layers. With npm:

```bash
ssh "$SSH_ALIAS" \
  "mkdir -p '$CODEX_CLI_DIR' '$CODEX_HOME_DIR' && npm install -g --prefix '$CODEX_CLI_DIR' @openai/codex@latest && '$CODEX_CLI_DIR/bin/codex' --version"
```

If the remote uses a standalone tree such as `/lpai/.codex-ALIAS-home/packages/standalone/current`, install or copy the newer compatible Linux x64 standalone release under `packages/standalone/releases/<version>-x86_64-unknown-linux-musl`, then move the `current` symlink atomically:

```bash
ssh "$SSH_ALIAS" \
  "ln -sfn '$CODEX_HOME_DIR/packages/standalone/releases/VERSION-x86_64-unknown-linux-musl' '$CODEX_HOME_DIR/packages/standalone/current' && '$CODEX_HOME_DIR/packages/standalone/current/bin/codex' --version"
```

After any CLI upgrade, confirm `/usr/local/bin/codex` executes the intended path. Rewrite the wrapper if it still points at an old CLI directory, then restart the app-server:

```bash
ssh -o ClearAllForwardings=yes "$SSH_ALIAS" \
  'for pid in $(ps -eo pid,args | awk '\''/codex app-server|app-server proxy/ && !/awk/ {print $1}'\''); do kill "$pid" 2>/dev/null || true; done; rm -rf "$CODEX_HOME/app-server-control" "$CODEX_HOME/app-server-daemon" /root/.codex/app-server-control /root/.codex/app-server-daemon; codex --version; codex app-server daemon version 2>/dev/null || true'
```

Do not treat a version upgrade as complete until both `codex --version` and the live app-server version report the intended version, and a small `codex exec` request succeeds.

## Wrapper

Write `/usr/local/bin/codex` on the remote:

```bash
#!/usr/bin/env bash
export CODEX_HOME="${CODEX_HOME:-REMOTE_WORKDIR/.codex/home}"
export HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:18080}"
export HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:18080}"
export ALL_PROXY="${ALL_PROXY:-http://127.0.0.1:18080}"
if ! command -v node >/dev/null 2>&1; then
  for d in /root/.vscode-server/bin/* /lpai/.vscode-server/bin/* /root/.vscode-remote-containers/bin/*; do
    if [ -x "$d/node" ]; then
      export PATH="$d:$PATH"
      break
    fi
  done
fi
exec REMOTE_WORKDIR/.codex/cli/bin/codex "$@"
```

Replace `REMOTE_WORKDIR` before writing. Then:

```bash
chmod 0755 /usr/local/bin/codex
```

For long workspaces, replace the wrapper `CODEX_HOME` with the short home path:

```bash
export CODEX_HOME="${CODEX_HOME:-/lpai/.codex-ALIAS-home}"
```

Keep the final `exec .../.codex/cli/bin/codex "$@"` pointing at the real CLI path.

## Auth and Config

Copy auth without displaying it:

```bash
scp -p ~/.codex/auth.json "$SSH_ALIAS:/tmp/codex-auth.json"
ssh "$SSH_ALIAS" "mkdir -p '$CODEX_HOME_DIR' /root/.codex; cp /tmp/codex-auth.json '$CODEX_HOME_DIR/auth.json'; mv /tmp/codex-auth.json /root/.codex/auth.json; chmod 600 '$CODEX_HOME_DIR/auth.json' /root/.codex/auth.json"
```

Write both `${CODEX_HOME_DIR}/config.toml` and `/root/.codex/config.toml`:

```toml
approval_policy = "never"
sandbox_mode = "danger-full-access"

[projects."REMOTE_WORKDIR"]
trust_level = "trusted"

[projects."/lpai"]
trust_level = "trusted"

[tui.model_availability_nux]
"gpt-5.5" = 1

[features]
network_proxy = true
```

Add parent repo paths such as `/lpai/code` when appropriate.

Also trust canonical symlink targets when the repo path resolves through `/mnt/volumes`, for example:

```toml
[projects."/mnt/volumes/.../repo"]
trust_level = "trusted"
```

## Restart and Validate

Stop stale servers:

```bash
ssh -o ClearAllForwardings=yes "$SSH_ALIAS" \
  'for pid in $(ps -eo pid,args | awk '\''/codex app-server|app-server proxy/ && !/awk/ {print $1}'\''); do kill "$pid" 2>/dev/null || true; done; rm -rf "$CODEX_HOME/app-server-control" "$CODEX_HOME/app-server-daemon" /root/.codex/app-server-control /root/.codex/app-server-daemon'
```

Validate:

```bash
ssh "$SSH_ALIAS" 'codex --version; codex login status'
ssh "$SSH_ALIAS" 'codex app-server daemon version 2>/dev/null || true'
ssh "$SSH_ALIAS" 'curl -I --proxy http://127.0.0.1:18080 --connect-timeout 8 https://api.openai.com 2>&1 | sed -n "1,30p"'
ssh "$SSH_ALIAS" 'codex doctor --summary 2>/dev/null | sed -n "1,160p"'
ssh "$SSH_ALIAS" "cd '$REMOTE_WORKDIR' && codex exec --skip-git-repo-check -C '$REMOTE_WORKDIR' 'Run pwd using shell and answer with the path only.'"
```

Success signs:

```text
Logged in using ChatGPT
approval: never
sandbox: danger-full-access
HTTP/1.1 200 Connection established
codex exec returns REMOTE_WORKDIR
```

## Troubleshooting

- `codex: command not found`: restore `/usr/local/bin/codex` wrapper.
- `codex doctor` shows `updates ... available`: upgrade the active CLI, rewrite stale wrappers if needed, kill app-server/proxy processes, and verify the live app-server version. A green SSH check with an old app-server can still fail newer Desktop protocol features.
- `/usr/bin/env: node: No such file or directory`: add `/root/.vscode-server/bin/*`, `/lpai/.vscode-server/bin/*`, or `/root/.vscode-remote-containers/bin/*` to wrapper PATH.
- `Not logged in`: copy local `~/.codex/auth.json` to both project home and `/root/.codex`.
- `bwrap: Failed to make / slave`: set `sandbox_mode = "danger-full-access"` for a trusted remote.
- command approval prompts still appear: current Codex App task was likely created before config changes. Start a new task or change the current task's UI permission mode.
- `stream disconnected before completion`: run `codex doctor`; if websocket/reachability is currently OK, retry. If not, validate proxy curl and RemoteForward.
- `Error: path must be shorter than SUN_LEN`: shorten `CODEX_HOME`, usually to `/lpai/.codex-<alias>-home`, then remove stale app-server control directories and restart the App session.
- WebSocket fails while proxy curl succeeds: add `[features] network_proxy = true` to both the active `CODEX_HOME/config.toml` and `/root/.codex/config.toml`, then restart app-server.
- `remote port forwarding failed for listen port 18080`: another connection may already own the remote port. With `ExitOnForwardFailure no`, validate actual proxy use before changing ports.
