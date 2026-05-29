# Raoyixi Skills

Personal Codex skills packaged as a Codex plugin marketplace repository.

## Install

```bash
git clone https://github.com/Yixi-Rao/raoyixi-skills.git
cd raoyixi-skills
./install.sh
```

The installer registers the local marketplace, copies the plugin into Codex's runtime plugin cache, and enables:

```toml
[plugins."raoyixi-skills@raoyixi-skills"]
enabled = true
```

Restart Codex after installation. To verify from a shell:

```bash
codex debug prompt-input "list skills" | rg "raoyixi-skills:"
```

## Contents

The plugin lives at `plugins/raoyixi-skills` and exposes the skills under `plugins/raoyixi-skills/skills`.

This repository intentionally excludes symlinked local skills, AutoResearchClaw skills, duplicate `pua` and `lpai-download` copies, and project-bound `verl-0407` issue/PR skills.

## Safety

No auth files, private keys, cookies, raw tokens, local Codex state, or generated caches should be committed. Skills that mention credentials use placeholders, environment variables, or procedural warnings only.
