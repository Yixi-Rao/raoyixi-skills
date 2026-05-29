# auto-merge-request

## Purpose

Create and manage a review-ready GitLab merge request from a local repository, including branch push, issue creation, issue/MR closing-link association, and verification that merge will close the issue.

## Required Inputs

- Target repository path.
- Target branch. Infer from context only when the branch is unambiguous; otherwise ask.
- Issue title and problem-focused issue description. Generate them from the diff when the user asks you to handle the whole flow.

## Rules

- Do not print tokens, `auth.json`, or unredacted credential files.
- Prefer HTTPS GitLab remotes with `git credential fill`.
- A completed MR must be `opened`, not Draft/WIP, have a pushed source branch, and have a related issue.
- `approve` does not close issues. GitLab closes issues after merge when the MR description or commit message contains `Closes #N`, `Fixes #N`, or `Resolves #N`.
- Target the GitLab project default branch by default. If a requested target branch is not the project default branch, stop and explain that issue auto-close may not run unless the user explicitly accepts a non-default target.
- For multiple repositories or worktrees, complete the full checklist per path. Do not count a worktree as done until its intended branch has committed changes, an upstream remote branch, and a matching MR.
- Preserve unrelated user changes. Stage only files intended for the requested MR.

## Workflow

1. Inspect the repository:
   ```bash
   git rev-parse --show-toplevel
   git rev-parse --git-dir
   git rev-parse --git-common-dir
   git remote -v
   git branch --show-current
   git status --short --branch
   git log -1 --oneline
   ```

2. Commit intended changes when the user has confirmed they should be included:
   ```bash
   git add <intended-files>
   git commit -m "<message>"
   ```

3. Ensure credential helper works. In devcontainers with a broken injected helper, reset locally:
   ```bash
   git config --local --add credential.helper ''
   git config --local --add credential.helper store
   ```

4. Push and verify upstream:
   ```bash
   git push -u origin HEAD
   git rev-parse --abbrev-ref --symbolic-full-name '@{u}'
   git ls-remote --heads origin "$(git branch --show-current)"
   ```

5. Use the helper script for GitLab API operations:
   ```bash
   python3 <skill-dir>/scripts/gitlab_auto_mr.py \
     --issue-title "<issue title>" \
     --issue-description "<issue body>"
   ```

   Pass `--target-branch <target-branch>` only when the requested target is explicit. The helper defaults to the GitLab project default branch and rejects non-default targets unless `--allow-non-default-target` is provided.

   Reuse existing objects when appropriate:
   ```bash
   python3 <skill-dir>/scripts/gitlab_auto_mr.py \
     --issue-iid <issue-iid> \
     --mr-iid <mr-iid> \
     --issue-title "<issue title>" \
     --issue-description "<issue body>"
   ```

6. Verify output:
   - Issue state is `opened` when the MR is expected to close a currently open problem.
   - MR state is `opened`.
   - MR is not Draft/WIP.
   - `detailed_merge_status` is acceptable or reported as a blocker.
   - `related_merge_requests` contains the MR.
   - MR description includes both a readable issue title and `Closes #N`.
   - `target_branch` equals `default_branch` unless a non-default target was explicitly accepted.
   - `warnings` is empty, or any warning is explained in the final response.

## MR Description Pattern

```text
Related issue: #ISSUE_IID Issue title here

Closes #ISSUE_IID

Source branch: source/name
Target branch: target/name

HEAD: abc1234 commit subject
```

GitLab may need a few seconds to index a new closing reference; retry related-MR verification before declaring failure.
