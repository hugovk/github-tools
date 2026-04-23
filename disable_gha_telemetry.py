"""Disable GitHub Actions telemetry by setting `GH_TELEMETRY=false` and
`DO_NOT_TRACK=true` Actions variables for orgs and user repos.

Use:
    uv run ~/Dropbox/stufftodelete/disable_gha_telemetry.py --help

If you get this for orgs:
    HTTP 403: You must be an org admin or have the
    actions variables fine-grained permission.

Run:
    gh auth refresh -h github.com -s admin:org

To remove, re-login with basic permissions:
    gh auth login -h github.com
"""

# /// script
# requires-python = ">=3.10"
# dependencies = ["termcolor"]
# ///
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any

from termcolor import cprint

VARIABLES = {
    "DO_NOT_TRACK": "true",
    "GH_TELEMETRY": "false",
}


def gh(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True)


def set_org_variables(org: str, *, dry_run: bool) -> None:
    for name, value in VARIABLES.items():
        if dry_run:
            cprint(f"  [dry-run] gh variable set {name} --org {org}", "yellow")
        else:
            try:
                gh("variable", "set", name, "--body", value, "--org", org)
                cprint(f"  Set {name}={value}", "green")
            except subprocess.CalledProcessError as e:
                cprint(
                    f"  Failed to set {name}: {e.stderr.strip()}",
                    "red",
                    file=sys.stderr,
                )


def get_user_repos(user: str) -> list[dict[str, Any]]:
    result = gh(
        "repo",
        "list",
        user,
        "--no-archived",
        "--source",
        "--json",
        "nameWithOwner",
        "--limit",
        "999",
    )
    return json.loads(result.stdout)


def set_repo_variables(repo: str, *, dry_run: bool) -> bool:
    """Set variables on a repo. Returns False if the repo has no Actions API."""
    for name, value in VARIABLES.items():
        if dry_run:
            cprint(f"  [dry-run] gh variable set {name} --repo {repo}", "yellow")
        else:
            try:
                gh("variable", "set", name, "--body", value, "--repo", repo)
                cprint(f"  Set {name}={value}", "green")
            except subprocess.CalledProcessError as e:
                if "HTTP 404" in e.stderr:
                    cprint("  Skipped (Actions not available)", "yellow")
                    return False
                cprint(
                    f"  Failed to set {name}: {e.stderr.strip()}",
                    "red",
                    file=sys.stderr,
                )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-r",
        "--repos",
        nargs="+",
        default=[],
        metavar="OWNER/REPO",
        help="set variables on these repos",
    )
    parser.add_argument(
        "-o",
        "--orgs",
        nargs="+",
        default=[],
        metavar="ORG",
        help="set variables on these organisations",
    )
    parser.add_argument(
        "-u",
        "--users",
        nargs="+",
        default=[],
        metavar="USER",
        help="set variables on all non-fork, non-archived repos for these users",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="print commands without running them",
    )
    args = parser.parse_args()

    if not args.repos and not args.orgs and not args.users:
        parser.error("Provide at least one --orgs, --users, or --repos")

    # Track processed repos to avoid duplicates
    done_repos: set[str] = set()

    for repo in args.repos:
        cprint(f"Repo: {repo}", "blue")
        set_repo_variables(repo, dry_run=args.dry_run)
        done_repos.add(repo)

    for org in args.orgs:
        cprint(f"Org: {org}", "cyan", attrs=["bold"])
        set_org_variables(org, dry_run=args.dry_run)

    for user in args.users:
        cprint(f"User: {user}", "cyan", attrs=["bold"])
        repos = get_user_repos(user)
        print(f"  Found {len(repos)} non-fork, non-archived repos")
        for repo in repos:
            name = repo["nameWithOwner"]
            if name in done_repos:
                cprint(f"  Repo: {name} (already done)", "yellow")
                continue
            cprint(f"  Repo: {name}", "blue")
            set_repo_variables(name, dry_run=args.dry_run)
            done_repos.add(name)


if __name__ == "__main__":
    main()
