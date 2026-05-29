#!/usr/bin/env python3
"""Generate a Codex SSH remote setup plan from a pasted ssh/scp command."""

from __future__ import annotations

import argparse
import os
import re
import shlex
from dataclasses import dataclass


@dataclass
class Remote:
    host: str
    user: str
    port: str
    identity: str


def parse_remote_command(command: str) -> Remote:
    parts = shlex.split(command)
    if not parts:
        raise SystemExit("empty command")

    port = "22"
    identity = ""
    user = ""
    host = ""

    i = 0
    while i < len(parts):
        part = parts[i]
        if part in ("-p", "-P") and i + 1 < len(parts):
            port = parts[i + 1]
            i += 2
            continue
        if part.startswith("-p") and part != "-p" and parts[0].endswith("ssh"):
            port = part[2:]
        if part.startswith("-P") and part != "-P" and parts[0].endswith("scp"):
            port = part[2:]
        if part == "-i" and i + 1 < len(parts):
            identity = parts[i + 1]
            i += 2
            continue
        if "@" in part and not part.startswith("-"):
            target = part
            if ":" in target and not target.startswith("["):
                target = target.split(":", 1)[0]
            match = re.match(r"(?P<user>[^@]+)@(?P<host>.+)", target)
            if match:
                user = match.group("user")
                host = match.group("host").strip("[]")
        i += 1

    if not host:
        raise SystemExit("could not parse host from command")
    if not user:
        user = os.environ.get("USER", "root")
    if not identity:
        identity = "~/.ssh/id_rsa"

    return Remote(host=host, user=user, port=port, identity=identity)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alias", required=True)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--ssh-command", required=True)
    parser.add_argument("--local-proxy-port", default="18080")
    parser.add_argument("--remote-proxy-port", default="18080")
    args = parser.parse_args()

    remote = parse_remote_command(args.ssh_command)
    cli_dir = f"{args.workdir}/.codex/cli"
    home_dir = f"{args.workdir}/.codex/home"

    print("# Extracted connection")
    print(f"alias={args.alias}")
    print(f"host={remote.host}")
    print(f"user={remote.user}")
    print(f"port={remote.port}")
    print(f"identity={remote.identity}")
    print(f"workdir={args.workdir}")
    print()

    print("# SSH config block")
    print(f"Host {args.alias}")
    print(f"  HostName {remote.host}")
    print(f"  User {remote.user}")
    print(f"  Port {remote.port}")
    print(f"  IdentityFile {remote.identity}")
    print("  StrictHostKeyChecking no")
    print(
        f"  RemoteForward 127.0.0.1:{args.remote_proxy_port} "
        f"127.0.0.1:{args.local_proxy_port}"
    )
    print("  ExitOnForwardFailure yes")
    print("  ServerAliveInterval 30")
    print("  ServerAliveCountMax 99999")
    print("  TCPKeepAlive yes")
    print()

    print("# Manual confirmations")
    print("【人工】确认允许 Codex 修改本机 ~/.ssh/config。")
    print(f"【人工】确认远端工作目录是 {args.workdir}，并允许创建 .codex。")
    print("【人工】如果远端不能访问 OpenAI/ChatGPT，确认允许本机作为代理出口。")
    print("【人工】仅在可信远端项目中确认 danger-full-access。")
    print("【人工】最后在 Codex App Connections 页面选择 SSH alias 和 workspace。")
    print()

    print("# Validation commands")
    print(f"ssh -G {args.alias} | grep -E '^(hostname|port|user|identityfile|remoteforward|exitonforwardfailure) '")
    print(f"ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes {args.alias} 'hostname; whoami; pwd'")
    print(f"ssh -o ConnectTimeout=8 {args.alias} 'command -v node || true; node --version 2>/dev/null || true; command -v npm || true; npm --version 2>/dev/null || true; ls -ld {args.workdir} 2>/dev/null || true'")
    print(f"ssh -o ConnectTimeout=8 {args.alias} 'set -e; mkdir -p {cli_dir} {home_dir}; npm install -g --prefix {cli_dir} @openai/codex; {cli_dir}/bin/codex --version'")
    print(f"scp -p ~/.codex/auth.json {args.alias}:{home_dir}/auth.json")
    print(f"ssh -o ConnectTimeout=8 {args.alias} 'chmod 600 {home_dir}/auth.json; codex login status'")
    print(f"ssh -o ConnectTimeout=8 {args.alias} 'cd {args.workdir} && codex exec --skip-git-repo-check -C {args.workdir} \"Run pwd using shell and answer with the path only.\"'")


if __name__ == "__main__":
    main()
