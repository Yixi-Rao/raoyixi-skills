---
name: lpai-download
description: Downloads LPAI training task output files (logs, tensorboard, checkpoints, etc.) from the LPAI component library. Use when user says "download training outputs", "download logs", "download tensorboard", "download checkpoints", "lpai download", "lpaiDownload", or asks to fetch training results from LPAI tasks. Handles lpai_asset SDK installation, authentication, and file downloading.
metadata:
  author: LPAI
  version: 1.0.0
  category: devops
  tags: [lpai, training, download, tensorboard, checkpoints, logs]
---

# LPAI Download

Downloads training task output files (logs, tensorboard, checkpoints, etc.) from the LPAI component library.

## Parameters

The user must provide the following three parameters:

- **task_name** (required): LPAI training task name, e.g. `rl_verl_raoyixi-b2feda8e`
- **download_path** (required): Local destination path, e.g. `/lpai/code/verl/verl`
- **prefix** (required): Folder prefix to download, e.g. `logs`, `tensorboard`, `checkpoints`

## Usage

```
$lpai-download <task_name> <download_path> <prefix>
```

Example:
```
$lpai-download rl_verl_raoyixi-b2feda8e /lpai/code/verl/verl tensorboard
```

## Instructions

CRITICAL: Execute the following steps in order. Do NOT skip any step. Validate each step before proceeding to the next.

### Step 1: Install or Update lpai_asset SDK

1. Uninstall the old version (if it exists):
```bash
pip uninstall lpai_asset -y
```

2. Install the latest version:
```bash
pip install lpai_asset -U -i https://artifactory.ep.chehejia.com/artifactory/api/pypi/liauto-pypi-l5/simple
```

Note: Since version 2.2.16, the lpai-asset SDK introduced the `nest-asyncio` package, which may conflict with certain async event loop packages (e.g. `uvloop`).

### Step 2: Verify Installation

Run:
```bash
lpa version
```

Expected output: `lpai-asset cli version: 2.3.x` or similar.

If `lpa` command is not found, the installation failed. Check pip output and retry.

### Step 3: Authenticate

Run:
```bash
lpa auth --env live --jwt_token <user_jwt_token>
```

CRITICAL: You MUST ask the user to provide their JWT token. Do NOT use any hardcoded or example token. JWT tokens expire and must be fresh.

On success, the output will show the user ID, available tenants, namespaces, and permission scopes. The config is saved to `/root/.lpai/conf.json`.

If authentication has already been done previously and `/root/.lpai/conf.json` exists, ask the user whether to skip this step or re-authenticate.

### Step 4: Download Task Outputs

Run:
```bash
lpa download tasks/{task_name} -path {download_path} -prefix {prefix}
```

Replace `{task_name}`, `{download_path}`, and `{prefix}` with the actual user-provided values.

Example:
```bash
lpa download tasks/rl_verl_raoyixi-b2feda8e -path /lpai/code/verl/verl -prefix tensorboard
```

### Step 5: Verify Download

After download completes, verify the files:
```bash
ls -lh {download_path}/{prefix}
```

Report the downloaded file list and total size to the user.

## Common Prefix Values

| Prefix | Description |
|---|---|
| `logs` | Training log files |
| `tensorboard` | TensorBoard visualization data |
| `checkpoints` | Model checkpoint files |
| `outputs` | Other output files |

## Examples

### Example 1: Download TensorBoard Data

User says: "Download the tensorboard data from task rl_verl_raoyixi-b2feda8e to /lpai/code/verl/verl"

Actions:
1. Install/update lpai_asset SDK
2. Verify installation with `lpa version`
3. Ask user for JWT token and authenticate
4. Run `lpa download tasks/rl_verl_raoyixi-b2feda8e -path /lpai/code/verl/verl -prefix tensorboard`
5. Verify download with `ls -lh /lpai/code/verl/verl/tensorboard`

Result: TensorBoard data downloaded and verified.

### Example 2: Download Checkpoints

User says: "$lpai-download rl_verl_raoyixi-b2feda8e /lpai/models checkpoints"

Actions:
1. Install/update lpai_asset SDK
2. Verify installation
3. Authenticate (ask for JWT token if needed)
4. Run `lpa download tasks/rl_verl_raoyixi-b2feda8e -path /lpai/models -prefix checkpoints`
5. Verify download

Result: Model checkpoints downloaded to /lpai/models/checkpoints.

## Troubleshooting

### Error: Authentication Failed
- **Cause**: JWT token is invalid, expired, or has extra whitespace
- **Solution**: Ask the user to provide a fresh JWT token. Ensure no trailing spaces when copying. Confirm `--env live` is used.

### Error: Download Failed
- **Cause**: Network issues, incorrect task name, or insufficient permissions
- **Solution**:
  1. Check network connectivity
  2. Confirm the task name is correct (case-sensitive)
  3. Verify the destination path exists and is writable: `mkdir -p {download_path}`
  4. Check the prefix spelling (case-sensitive)

### Error: Files Not Found
- **Cause**: Task may not have completed or generated the requested output type
- **Solution**:
  1. Confirm the task has completed and generated the output files
  2. Verify prefix spelling
  3. Contact the task admin for the list of available prefixes

### Error: Permission Denied
- **Cause**: User does not have access to the task
- **Solution**:
  1. Check user permissions for the task
  2. Verify namespace and tenant settings
  3. Contact admin to grant appropriate permissions

### Error: lpa Command Not Found
- **Cause**: lpai_asset SDK installation failed or not on PATH
- **Solution**:
  1. Re-run `pip install lpai_asset -U -i https://artifactory.ep.chehejia.com/artifactory/api/pypi/liauto-pypi-l5/simple`
  2. Check that `pip` matches the active Python environment
  3. Python 3.8+ is required

## Notes

- TensorBoard and log files are continuously updated during training; re-download periodically for latest data
- Ensure sufficient disk space before downloading (TensorBoard data can be large)
- Requires network access to `artifactory.ep.chehejia.com`
