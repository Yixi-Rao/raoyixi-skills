#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
MARKETPLACE_NAME="raoyixi-skills"
PLUGIN_NAME="raoyixi-skills"
PLUGIN_KEY="${PLUGIN_NAME}@${MARKETPLACE_NAME}"
PLUGIN_SRC="${REPO_ROOT}/plugins/${PLUGIN_NAME}"
PLUGIN_JSON="${PLUGIN_SRC}/.codex-plugin/plugin.json"

if [[ ! -f "${PLUGIN_JSON}" ]]; then
  echo "Missing plugin manifest: ${PLUGIN_JSON}" >&2
  exit 1
fi

VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "${PLUGIN_JSON}")"
CACHE_DST="${CODEX_HOME}/plugins/cache/${MARKETPLACE_NAME}/${PLUGIN_NAME}/${VERSION}"
CONFIG_FILE="${CODEX_HOME}/config.toml"

mkdir -p "${CODEX_HOME}" "$(dirname "${CACHE_DST}")"

if command -v codex >/dev/null 2>&1; then
  codex plugin marketplace remove "${MARKETPLACE_NAME}" >/dev/null 2>&1 || true
  codex plugin marketplace add "${REPO_ROOT}"
fi

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    "${PLUGIN_SRC}/" "${CACHE_DST}/"
else
  rm -rf "${CACHE_DST}"
  mkdir -p "${CACHE_DST}"
  cp -R "${PLUGIN_SRC}/." "${CACHE_DST}/"
fi

touch "${CONFIG_FILE}"
if grep -q '^\[plugins\."raoyixi-skills@raoyixi-skills"\]' "${CONFIG_FILE}"; then
  perl -0pi -e 's/(\[plugins\."raoyixi-skills\@raoyixi-skills"\]\s*\nenabled\s*=\s*)false/${1}true/s' "${CONFIG_FILE}"
else
  {
    printf '\n[plugins."%s"]\n' "${PLUGIN_KEY}"
    printf 'enabled = true\n'
  } >> "${CONFIG_FILE}"
fi

COUNT="$(find "${CACHE_DST}/skills" -maxdepth 2 -name SKILL.md -print | wc -l | tr -d ' ')"
echo "Installed ${PLUGIN_KEY} ${VERSION} into ${CACHE_DST}"
echo "Skills installed: ${COUNT}"
echo "Restart Codex, or verify with:"
echo "  codex debug prompt-input 'list skills' | rg 'raoyixi-skills:'"
