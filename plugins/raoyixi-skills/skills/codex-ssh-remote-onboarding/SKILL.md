---
name: codex-ssh-remote-onboarding
description: Onboard new Codex SSH remotes for Codex App/CLI on LPAI or similar remote Linux servers. Use when a user asks to set up or teach a new Codex remote-control / SSH Connections / remote exec workflow, including installing Codex on a remote host, copying auth.json, configuring proxy RemoteForward, selecting sandbox mode, and guiding required human approvals.
---

# Codex SSH Remote Onboarding

## Operating Model

Treat this as an assisted setup workflow, not a static explanation. Drive the configuration forward while clearly separating:

- `Codex 自动执行`: checks, command generation, SSH config edits, remote installation, auth copy, validation.
- `【人工】`: dynamic SSH command/port, local SSH config permission, remote install permission, proxy permission, sandbox trust decision, Codex App UI selection.

Never display private key contents, token values, or `auth.json` contents. Copy `auth.json` as a file only.

## Inputs To Collect

Ask only for missing inputs:

```text
1. LPAI/remote SSH or SCP command
2. desired SSH alias, for example lpai-zyy-dev
3. remote workdir, for example /lpai/code/rllm
4. whether remote project is trusted enough for danger-full-access
5. whether local machine may act as proxy outlet if remote cannot reach OpenAI/ChatGPT
```

If the user gives an `scp -P` command, parse it as SSH connection data: `-P` is the SSH port, the target `user@host:path` gives user and host, and `-i` gives identity file.

Use `references/remote-guide.md` only when command details or troubleshooting branches are needed.

## Workflow

1. `【人工】` Ask the user to paste the latest SSH/SCP command from the platform if the current SSH port is unknown or connection is refused.
2. Generate or update `~/.ssh/config` for `{SSH_ALIAS}`. Use `RemoteForward 127.0.0.1:{REMOTE_PROXY_PORT} 127.0.0.1:{LOCAL_PROXY_PORT}` only if proxy is needed or requested. Avoid reusing a remote proxy port already used by another Host.
3. Validate SSH parsing and basic login:
   ```bash
   ssh -G {SSH_ALIAS} | grep -E '^(hostname|port|user|identityfile|remoteforward|exitonforwardfailure) '
   ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes {SSH_ALIAS} 'hostname; whoami; pwd'
   ```
4. Validate remote environment:
   ```bash
   ssh -o ConnectTimeout=8 {SSH_ALIAS} 'command -v node || true; node --version 2>/dev/null || true; command -v npm || true; npm --version 2>/dev/null || true; ls -ld {REMOTE_WORKDIR} 2>/dev/null || true'
   ```
5. `【人工】` Confirm remote workdir and permission to create `{REMOTE_WORKDIR}/.codex`.
6. Install Codex under the project:
   ```bash
   ssh -o ConnectTimeout=8 {SSH_ALIAS} 'set -e; mkdir -p {REMOTE_WORKDIR}/.codex/cli {REMOTE_WORKDIR}/.codex/home; npm install -g --prefix {REMOTE_WORKDIR}/.codex/cli @openai/codex; {REMOTE_WORKDIR}/.codex/cli/bin/codex --version'
   ```
7. Write a stable remote wrapper at `/usr/local/bin/codex` so non-interactive SSH sessions use the intended `CODEX_HOME`, proxy, and CLI path.
8. Copy local auth by default:
   ```bash
   scp -p ~/.codex/auth.json {SSH_ALIAS}:{REMOTE_WORKDIR}/.codex/home/auth.json
   ssh -o ConnectTimeout=8 {SSH_ALIAS} 'chmod 600 {REMOTE_WORKDIR}/.codex/home/auth.json; codex login status'
   ```
   If this fails or the file is unavailable, guide `codex login --device-auth` as `【人工】` browser authorization.
9. Test remote network. If remote cannot reach OpenAI/ChatGPT, `【人工】` confirm local proxy outlet and add/check RemoteForward.
10. Test sandbox. If `bwrap` fails inside trusted LPAI/container workdir, `【人工】` confirm `danger-full-access`, then set:
    ```toml
    sandbox_mode = "danger-full-access"

    [projects."{REMOTE_WORKDIR}"]
    trust_level = "trusted"
    ```
11. Final validation:
    ```bash
    ssh -o ConnectTimeout=8 {SSH_ALIAS} 'cd {REMOTE_WORKDIR} && codex exec --skip-git-repo-check -C {REMOTE_WORKDIR} "Run pwd using shell and answer with the path only."'
    ```
12. `【人工】` In Codex App, open Settings -> Connections -> SSH, select `{SSH_ALIAS}`, then choose `{REMOTE_WORKDIR}` as workspace.

## Human Guidance Rules

For every `【人工】` step, tell the user:

- what to choose,
- why it cannot be safely inferred,
- what happens if they say no,
- the exact text or UI field to use.

Do not ask for confirmation for copying local `~/.codex/auth.json` when the user has already adopted this workflow. Still do not print the file.

When connection fails:

- `Connection refused`: ask for latest platform SSH command/port.
- `Could not resolve hostname`: check VPN/DNS/internal network.
- `Permission denied (publickey)`: check identity file path and file permissions.
- `remote port forwarding failed`: choose a different `{REMOTE_PROXY_PORT}`.
- missing Node/npm: ask whether to install Node/npm or switch image/environment.
- `bwrap: Failed to make / slave`: ask whether trusted project may use `danger-full-access`.

## Helper Script

Use `scripts/plan_remote_setup.py` to parse a pasted SSH/SCP command and print a setup plan:

```bash
python3 $HOME/.codex/skills/codex-ssh-remote-onboarding/scripts/plan_remote_setup.py \
  --alias lpai-zyy-dev \
  --workdir /lpai/code/rllm \
  --ssh-command 'scp -i key.pem -P 32421 file root@ssh-d.example.com:/lpai'
```

The script emits:

- extracted host/user/port/identity,
- an SSH config block,
- a manual confirmation checklist,
- validation commands.

## References

- `references/remote-guide.md`: full operation guide, command templates, screenshots, and troubleshooting.
