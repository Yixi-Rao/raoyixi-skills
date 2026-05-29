#!/usr/bin/env python3
"""Create a GitLab issue and review-ready MR, then link them with Closes #N."""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request


def run_git(args):
    result = subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def parse_project_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SystemExit(f"Only HTTP(S) GitLab remotes are supported: {url}")
    path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    if not path or "/" not in path:
        raise SystemExit(f"Could not infer GitLab project path from: {url}")
    return f"{parsed.scheme}://{parsed.netloc}", path


def credential_token(base_url):
    env_token = os.environ.get("GITLAB_TOKEN")
    if env_token:
        return env_token

    parsed = urllib.parse.urlparse(base_url)
    query = f"protocol={parsed.scheme}\nhost={parsed.netloc}\n\n"
    result = subprocess.run(
        ["git", "credential", "fill"],
        input=query,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit("Could not read GitLab token from git credential helper")
    for line in result.stdout.splitlines():
        if line.startswith("password="):
            token = line.split("=", 1)[1]
            if token:
                return token
    raise SystemExit("No password/token found in git credentials; set GITLAB_TOKEN or approve a credential")


class GitLab:
    def __init__(self, base_url, token, dry_run=False):
        self.api = base_url.rstrip("/") + "/api/v4"
        self.token = token
        self.dry_run = dry_run

    def request(self, method, path, data=None):
        url = self.api + path
        body = None
        headers = {"PRIVATE-TOKEN": self.token}
        if data is not None:
            body = urllib.parse.urlencode(data).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        if self.dry_run and method in {"POST", "PUT"}:
            print(json.dumps({"dry_run": True, "method": method, "url": url, "data": data}, ensure_ascii=False))
            return {}

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as response:
                raw = response.read().decode()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise SystemExit(f"GitLab API {method} {path} failed: HTTP {exc.code}: {detail}")
        return json.loads(raw) if raw else {}

    def get(self, path, query=None):
        if query:
            path += "?" + urllib.parse.urlencode(query)
        return self.request("GET", path)


def read_optional_text(value, file_path):
    if file_path:
        with open(file_path, "r", encoding="utf-8") as handle:
            return handle.read()
    return value or ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-url", default=None, help="HTTPS GitLab project URL; defaults to origin")
    parser.add_argument("--source-branch", default=None, help="Source branch; defaults to current branch")
    parser.add_argument("--target-branch", default=None, help="Target branch for the MR; defaults to project default branch")
    parser.add_argument(
        "--allow-non-default-target",
        action="store_true",
        help="Allow targeting a non-default branch; issue auto-close may not run after merge",
    )
    parser.add_argument("--mr-title", default=None, help="MR title; defaults to HEAD subject")
    parser.add_argument("--mr-iid", type=int, default=None, help="Existing MR IID to update instead of creating one")
    parser.add_argument("--issue-iid", type=int, default=None, help="Existing issue IID to link instead of creating one")
    parser.add_argument("--issue-title", default=None, help="Issue title; required unless --issue-iid is used")
    parser.add_argument("--issue-description", default=None, help="Issue description text")
    parser.add_argument("--issue-description-file", default=None, help="File containing issue description")
    parser.add_argument("--no-create-mr", action="store_true", help="Create/update issue only")
    parser.add_argument("--verify-retries", type=int, default=5, help="Poll related MRs this many times after writes")
    parser.add_argument("--verify-delay", type=float, default=1.0, help="Seconds between verification retries")
    parser.add_argument("--dry-run", action="store_true", help="Print write operations without executing them")
    args = parser.parse_args()

    if not args.issue_iid and not args.issue_title:
        parser.error("--issue-title is required unless --issue-iid is used")

    project_url = args.project_url or run_git(["config", "--get", "remote.origin.url"])
    base_url, project_path = parse_project_url(project_url)
    project_id = urllib.parse.quote(project_path, safe="")
    source_branch = args.source_branch or run_git(["branch", "--show-current"])
    head = run_git(["log", "-1", "--pretty=format:%h %s"])
    mr_title = args.mr_title or run_git(["log", "-1", "--pretty=format:%s"])
    issue_description = read_optional_text(args.issue_description, args.issue_description_file)

    token = credential_token(base_url)
    gitlab = GitLab(base_url, token, args.dry_run)
    warnings = []

    project = gitlab.get(f"/projects/{project_id}")
    default_branch = project.get("default_branch")
    target_branch = args.target_branch or default_branch
    if not target_branch:
        raise SystemExit("Could not determine target branch; pass --target-branch explicitly")
    if default_branch and target_branch != default_branch:
        message = (
            f"Target branch '{target_branch}' is not the project default branch '{default_branch}'. "
            "GitLab issue auto-close normally runs when the MR is merged into the default branch."
        )
        if not args.allow_non_default_target:
            raise SystemExit(message + " Pass --allow-non-default-target to override.")
        warnings.append(message)

    if args.issue_iid:
        issue = gitlab.get(f"/projects/{project['id']}/issues/{args.issue_iid}")
        update_issue = {}
        if args.issue_title and args.issue_title != issue.get("title"):
            update_issue["title"] = args.issue_title
        if issue_description:
            update_issue["description"] = issue_description
        if update_issue:
            issue = gitlab.request("PUT", f"/projects/{project['id']}/issues/{args.issue_iid}", update_issue)
    else:
        issue = gitlab.request(
            "POST",
            f"/projects/{project['id']}/issues",
            {"title": args.issue_title, "description": issue_description},
        )
    issue_iid = issue.get("iid", "ISSUE_IID")
    issue_title = args.issue_title or issue.get("title", "")
    if args.issue_iid and issue.get("state") and issue.get("state") != "opened":
        warnings.append(
            f"Issue #{issue_iid} is {issue.get('state')}; use a new issue if this MR should close a newly-opened problem."
        )

    mr_description = (
        f"Related issue: #{issue_iid} {issue_title}\n\n"
        f"Closes #{issue_iid}\n\n"
        f"Source branch: {source_branch}\n"
        f"Target branch: {target_branch}\n\n"
        f"HEAD: {head}"
    )

    mr = None
    if not args.no_create_mr:
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": mr_title,
            "description": mr_description,
            "remove_source_branch": "false",
            "squash": "false",
        }
        mr_iid = args.mr_iid
        if not mr_iid:
            existing_mrs = gitlab.get(
                f"/projects/{project['id']}/merge_requests",
                {
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "state": "opened",
                },
            )
            if existing_mrs:
                mr_iid = existing_mrs[0]["iid"]
        if mr_iid:
            mr = gitlab.request("PUT", f"/projects/{project['id']}/merge_requests/{mr_iid}", data)
        else:
            mr = gitlab.request("POST", f"/projects/{project['id']}/merge_requests", data)

    related = []
    if issue.get("iid"):
        for attempt in range(max(args.verify_retries, 1)):
            related = gitlab.get(f"/projects/{project['id']}/issues/{issue['iid']}/related_merge_requests")
            if not mr or any(item.get("iid") == mr.get("iid") for item in related):
                break
            if attempt + 1 < args.verify_retries:
                time.sleep(args.verify_delay)
    if mr and mr.get("iid"):
        mr = gitlab.get(f"/projects/{project['id']}/merge_requests/{mr['iid']}")

    output = {
        "project": project.get("path_with_namespace"),
        "default_branch": default_branch,
        "target_branch": target_branch,
        "issue": {
            "iid": issue.get("iid"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "web_url": issue.get("web_url"),
        },
        "merge_request": None if mr is None else {
            "iid": mr.get("iid"),
            "state": mr.get("state"),
            "draft": mr.get("draft"),
            "work_in_progress": mr.get("work_in_progress"),
            "detailed_merge_status": mr.get("detailed_merge_status"),
            "source_branch": mr.get("source_branch"),
            "target_branch": mr.get("target_branch"),
            "web_url": mr.get("web_url"),
        },
        "related_merge_requests": [
            {
                "iid": item.get("iid"),
                "state": item.get("state"),
                "draft": item.get("draft"),
                "work_in_progress": item.get("work_in_progress"),
                "detailed_merge_status": item.get("detailed_merge_status"),
                "source_branch": item.get("source_branch"),
                "target_branch": item.get("target_branch"),
                "web_url": item.get("web_url"),
            }
            for item in related
        ],
        "warnings": warnings,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
