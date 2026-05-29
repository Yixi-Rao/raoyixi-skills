#!/usr/bin/env bash
set -uo pipefail

alias_name="${1:-}"
workdir="${2:-}"
remote_proxy="${3:-127.0.0.1:18080}"

if [[ -z "$alias_name" || -z "$workdir" ]]; then
  echo "Usage: $0 <ssh-alias> <remote-workdir> [remote-proxy-host:port]" >&2
  exit 2
fi

section() {
  printf '\n== %s ==\n' "$1"
}

section "ssh -G"
ssh -G "$alias_name" 2>/dev/null | grep -E '^(hostname|port|user|identityfile|remoteforward|exitonforwardfailure) ' || true

section "basic ssh"
ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$alias_name" 'hostname; whoami; pwd' || true

section "remote workspace"
ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$alias_name" "ls -ld '$workdir' '$workdir/.codex' '$workdir/.codex/cli' '$workdir/.codex/home' 2>/dev/null || true" || true

section "remote codex"
ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$alias_name" 'command -v codex || true; codex --version 2>&1 || true; codex login status 2>&1 || true' || true

section "remote config"
ssh -o ConnectTimeout=8 -o ClearAllForwardings=yes "$alias_name" "sed -n '1,120p' '$workdir/.codex/home/config.toml' 2>/dev/null || true" || true

section "proxy curl"
ssh -o ConnectTimeout=8 "$alias_name" "curl -I --proxy http://$remote_proxy --connect-timeout 8 https://api.openai.com 2>&1 | sed -n '1,30p'" || true

section "doctor summary"
ssh -o ConnectTimeout=8 "$alias_name" 'codex doctor --summary 2>/dev/null | sed -n "1,160p"' || true
