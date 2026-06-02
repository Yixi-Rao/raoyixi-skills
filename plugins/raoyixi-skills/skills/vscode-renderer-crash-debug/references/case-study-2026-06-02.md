# 2026-06-02 VS Code Remote-SSH Renderer Crash Case Study

Use this reference when the live evidence resembles a VS Code macOS dialog:

`The window terminated unexpectedly (reason: 'crashed', code: '5')`

## High-confidence Root Boundary

The hard failure boundary was the local VS Code Electron renderer:

- `main.log`: `CodeWindow: renderer process gone (reason: crashed, code: 5)`
- Crashpad dump strings: `Code Helper (Renderer)`, `Electron Framework`, `--type=renderer`
- Extension host exited after renderer death: `renderer closed the MessagePort`, exit code `0`
- Remote SSH resolved successfully before the crash, so Remote-SSH was the active workspace surface, not the proven root cause.

## Evidence Timeline

- `16:32`, `16:54`, `16:58`: repeated renderer crash dumps and `main.log` entries.
- First suspect: `lqyld.vscode-icons-iconify` conflicted with `vscode-icons-team.vscode-icons`.
  - Evidence: `Command vscode-icons.activateIcons already registered`.
  - Action: moved `lqyld.vscode-icons-iconify-0.1.2` out of `~/.vscode/extensions`, removed it from `extensions.json`.
  - Result: crash still occurred at `17:14`, so this was a real bad extension but not the full root cause.
- Second suspect: `cliffordfajardo.hightlight-selections-vscode`.
  - Evidence: repeated `FAILED to handle event` in extension host logs.
  - Extension characteristics: version `0.0.1`, VS Code engine `^1.19.0`, `activationEvents: ["*"]`, selection decorations on every window.
  - Action: moved it out of `~/.vscode/extensions`, removed it from `extensions.json`.
  - Result: crash still occurred at `17:31`, so it was not the full root cause.
- Main root chain: built-in `GitHub.copilot-chat` plus CopilotCLI/Claude chat sessions.
  - Evidence in `window7`:
    - `ExtensionService#_doActivateExtension GitHub.copilot-chat`
    - `CopilotCLI MCP server started`
    - `chatParticipant must be declared in package.json: copilot-cloud-agent`
    - `chatParticipant must be declared in package.json: copilotcli`
    - `chatParticipant must be declared in package.json: claude-code`
    - renderer crashed soon after.
  - `anthropic.claude-code` was also active in the same chain.
  - Action: persistent disablement of `github.copilot-chat` and `github.copilot`; moved the built-in Copilot Chat extension directory out of the VS Code app bundle; moved `anthropic.claude-code` out of user extensions.
  - Result: new `window8` no longer showed `GitHub.copilot-chat`, `CopilotCLI`, or `chatParticipant must be declared`; no new dump appeared during the immediate soak window.

## Known Local Versions

- VS Code: `1.122.1`
- Commit: `8761a5560cfd65fdd19ce7e2bd18dab5c0a4d84e`
- Built-in `GitHub.copilot-chat`: `0.50.1`
- `GitHub.copilot-chat` manifest engine: `vscode ^1.122.1`
- Conclusion: not simply "user installed an old Copilot Chat". It was a built-in extension/runtime state inconsistency.

## Failed or Insufficient Fixes

Do not stop after these if a new Crashpad dump appears:

- Removing only `lqyld.vscode-icons-iconify`.
- Removing only `cliffordfajardo.hightlight-selections-vscode`.
- Adding only Copilot subfeature settings such as:
  - `github.copilot.chat.backgroundAgent.enabled: false`
  - `github.copilot.chat.cloudAgent.enabled: false`
  - `github.copilot.chat.claudeAgent.enabled: false`
  - `github.copilot.chat.cli.mcp.enabled: false`
  - `github.copilot.chat.cli.remote.enabled: false`

Those settings did not prevent `GitHub.copilot-chat` from activating or starting CopilotCLI in the observed case.

## Repair Ladder

Apply each step only when the evidence supports it. Verify after each step by reopening VS Code and checking for new `main.log` crashes and Crashpad dumps.

1. Preserve user work.
   - Do not force quit if the UI has unsaved tabs.
   - Use the crash dialog `Reopen` only after file-system changes are ready.
2. Confirm local renderer crash.
   - `main.log` must show `CodeWindow: renderer process gone`.
   - Crashpad dump must identify `Code Helper (Renderer)`.
3. Separate Remote-SSH from renderer.
   - If `resolveAuthority(ssh-remote)` returned `WebSocket(127.0.0.1:PORT)` and sockets were created, Remote-SSH connection is not the primary failure.
4. Isolate clearly broken user extensions.
   - Move the extension directory to `~/.vscode/extensions-disabled/`.
   - Remove the extension id from `~/.vscode/extensions/extensions.json`.
   - Back up `extensions.json` first.
5. If Copilot Chat chain persists, disable and isolate it.
   - Add `github.copilot-chat` and `github.copilot` to `extensionsIdentifiers/disabled` in `User/globalStorage/state.vscdb`.
   - Back up the database first.
   - Move `/Applications/Visual Studio Code.app/Contents/Resources/app/extensions/copilot` to `~/.vscode/extensions-disabled-builtin/`.
   - Move `anthropic.claude-code-*` to `~/.vscode/extensions-disabled/` if `claude-code` participant errors appear.
6. Verify the negative evidence.
   - New window logs should not show `GitHub.copilot-chat`, `CopilotCLI`, or `chatParticipant must be declared`.
   - `main.log` should have no newer renderer crash.
   - Crashpad should have no newer `.dmp`.

## Rollback

Use rollback if the user needs Copilot Chat back after a VS Code update/reinstall.

- Restore built-in Copilot Chat:
  - Move `~/.vscode/extensions-disabled-builtin/copilot-builtin-*/` back to `/Applications/Visual Studio Code.app/Contents/Resources/app/extensions/copilot`.
- Restore Claude Code:
  - Move `~/.vscode/extensions-disabled/anthropic.claude-code-*` back to `~/.vscode/extensions/`.
  - Restore or edit `~/.vscode/extensions/extensions.json`.
- Restore VS Code global disabled ids:
  - Restore `~/Library/Application Support/Code/User/globalStorage/state.vscdb.bak-*`, or remove `github.copilot-chat` and `github.copilot` from `extensionsIdentifiers/disabled`.

Prefer reinstalling or updating VS Code instead of manually restoring the app-bundle extension when available.

## Evidence Commands

```bash
tail -n 80 "$HOME/Library/Application Support/Code/logs/<session>/main.log"
find "$HOME/Library/Application Support/Code/Crashpad/completed" -maxdepth 1 -type f -name '*.dmp' -newermt '<local time>' -print
strings -a "$HOME/Library/Application Support/Code/Crashpad/completed/<dump>.dmp" | rg 'Code Helper|Electron|--type=renderer|--vscode-window-config|VSCODE_PID'
rg -n 'renderer process gone|GitHub.copilot-chat|CopilotCLI|chatParticipant|claude-code|FAILED to handle event|resolveAuthority' "$HOME/Library/Application Support/Code/logs/<session>"
```
