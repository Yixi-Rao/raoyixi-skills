# Codex SSH Remote Onboarding Reference

This reference is copied from the validated operation guide. Load it when the user needs exact command templates, detailed troubleshooting, or screenshot-backed manual instructions.

Source guide path:

```text
$HOME/programs/lixiang/agent_create_code/prompts/codex配置/ssh配置.guide.md
```

Feishu version:

```text
https://li.feishu.cn/docx/VayedSQ6DoXaLfxcc5ucEpAAnY1
```

## Command Variables

```text
{SSH_ALIAS}        remote SSH alias, for example lpai-zyy-dev
{REMOTE_WORKDIR}   remote project/work directory, for example /lpai/code/rllm
{CODEX_CLI_DIR}    {REMOTE_WORKDIR}/.codex/cli
{CODEX_HOME_DIR}   {REMOTE_WORKDIR}/.codex/home
{LOCAL_PROXY_PORT} local CONNECT proxy port, usually 18080
{REMOTE_PROXY_PORT} remote forwarded proxy port, one per SSH Host
```

## Full Setup Checklist

1. Parse the latest platform SSH/SCP command.
2. Update `~/.ssh/config` for `{SSH_ALIAS}`.
3. Verify `ssh -G` and basic login.
4. Verify Node/npm and `{REMOTE_WORKDIR}`.
5. Install Codex into `{CODEX_CLI_DIR}`.
6. Write `/usr/local/bin/codex` wrapper.
7. Copy local `~/.codex/auth.json` to `{CODEX_HOME_DIR}/auth.json` and `chmod 600`.
8. Verify `codex login status`.
9. Verify remote OpenAI/ChatGPT network or configure RemoteForward proxy.
10. Configure sandbox only after trust decision.
11. Run final `codex exec` pwd validation.
12. Guide user through Codex App Settings -> Connections -> SSH selection.

## Wrapper Template

```bash
#!/usr/bin/env bash
export CODEX_HOME="${CODEX_HOME:-{CODEX_HOME_DIR}}"
export HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:{REMOTE_PROXY_PORT}}"
export HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:{REMOTE_PROXY_PORT}}"
export ALL_PROXY="${ALL_PROXY:-http://127.0.0.1:{REMOTE_PROXY_PORT}}"
exec {CODEX_CLI_DIR}/bin/codex "$@"
```

## Sandbox Config Template

```toml
sandbox_mode = "danger-full-access"

[projects."{REMOTE_WORKDIR}"]
trust_level = "trusted"
```

Use this only after `【人工】` trust confirmation for the remote machine and project directory.

## Troubleshooting Matrix

| Symptom | Likely Cause | Action |
| --- | --- | --- |
| `Connection refused` | Dynamic SSH port changed | `【人工】` Ask for latest platform SSH command and update port |
| `Could not resolve hostname` | VPN/DNS/internal network issue | Ask user to check VPN and internal network |
| `Permission denied (publickey)` | Wrong identity file or permissions | Verify `IdentityFile`, `chmod 600` private key |
| `remote port forwarding failed` | Remote proxy port already used | Pick a new `{REMOTE_PROXY_PORT}` such as `18081` |
| missing `node`/`npm` | Image lacks Node runtime | `【人工】` Ask whether to install Node/npm or switch image |
| `Not logged in` | Auth not copied or invalid | Copy `auth.json`, or guide device-auth login |
| `bwrap: Failed to make / slave` | Container sandbox incompatibility | `【人工】` For trusted projects, allow `danger-full-access` |
| `codex exec` cannot find project | Wrong `-C` or missing directory | Reconfirm `{REMOTE_WORKDIR}` |

## Manual UI Guidance

For Codex App:

```text
Settings -> Connections -> SSH -> Add/Select SSH connection -> choose {SSH_ALIAS}
Workspace -> choose {REMOTE_WORKDIR}
```

If the App shows connection failed, first validate the same alias in terminal with:

```bash
ssh -o ConnectTimeout=8 {SSH_ALIAS} 'hostname; whoami; pwd'
```

Terminal success plus App failure usually indicates the App is using a different SSH config, different shell environment, or missing remote `codex` wrapper.
