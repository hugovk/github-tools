"""
Go through each merged PR with a "needs backport to 3.x" label and check
if there is a commit on the corresponding branch that refers to that PR.

Some PRs have those labels but:

* the backport was manually done and the label is still there, or
* the backport is missing and was forgotten about, or
* the backport was deliberately held up
"""

# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "ghapi",
#     "rich",
# ]
# ///

from __future__ import annotations

import argparse
import os
import subprocess
from collections import defaultdict
from functools import cache
from typing import Any, TypeAlias

from ghapi.all import GhApi, paged  # pip install ghapi
from rich import print  # pip install rich

from potential_closeable_issues import sort_by_to_sort_and_direction

PR: TypeAlias = dict[str, Any]


GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]


@cache
def get_pr_commit(api: GhApi, pull_number: int) -> str:
    return api.pulls.get(pull_number=pull_number).merge_commit_sha


@cache
def get_title_of_commit(repo_path: str, commit_sha: str) -> str:
    return (
        subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B", commit_sha], cwd=repo_path
        )
        .decode("utf-8")
        .split("\n")[0]
    )


@cache
def is_commit_title_in_branch(repo_path: str, title: str, branch: str) -> bool:
    # TODO make sure title is escaped for grep
    output = subprocess.check_output(
        ["git", "log", "--grep", title, branch], cwd=repo_path
    ).decode("utf-8")
    return output != ""


def check_prs(
    api: GhApi,
    repo_path: str,
    branch_to_check: str,
    start: int = 1,
    number: int = 100,
    sort_by: str = "newest",
) -> dict[str, list[PR]]:
    sort, direction = sort_by_to_sort_and_direction(sort_by)
    candidates = defaultdict(list)  # reason => PRs
    pr_count = 0
    for page in paged(
        # The PR API doesn't filter by label.
        # PR are really issues, so use the issues API.
        api.issues.list_for_repo,
        state="closed",
        sort=sort,
        direction=direction,
        per_page=100,
        labels=f"needs backport to {branch_to_check}",
    ):
        for pr in page:
            pr_count += 1
            print(pr_count, start, number, pr.html_url)

            if pr_count < start:
                continue

            if pr_count >= start + number:
                return candidates

            if "/issues/" in pr.html_url:
                print("    [red]Issue with backport labels[/red]")
                candidates["issues with backport labels"].append(pr)
                continue

            if not pr.pull_request.merged_at:
                # PR was closed without being merged, skip it
                continue
            commit = get_pr_commit(api, pr.number)
            title = get_title_of_commit(repo_path, commit)
            print(f"  {title}")

            if is_commit_title_in_branch(repo_path, title, branch_to_check):
                print("    [red]Backport found, remove label?[/red]")
                candidates["with backports, remove label?"].append(pr)
            else:
                print(f"    [yellow]Backport to {branch_to_check} missing[/yellow]")
                candidates["missing backports"].append(pr)

    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("repo_path", help="path to CPython repo")
    parser.add_argument(
        "-b",
        "--branches",
        default="3.13,3.12,3.11,3.10,3.9",
        help="branches to check",
    )
    parser.add_argument(
        "-s", "--start", default=1, type=int, help="start at this PR number"
    )
    parser.add_argument(
        "-n", "--number", default=100, type=int, help="number of PRs to check"
    )
    parser.add_argument(
        "--sort",
        default="newest",
        choices=(
            "newest",
            "oldest",
            "most-commented",
            "least-commented",
            "recently-updated",
            "least-recently-updated",
        ),
        help="Sort by",
    )
    parser.add_argument(
        "-o", "--open-prs", action="store_true", help="open PRs in browser"
    )
    args = parser.parse_args()

    api = GhApi(owner="python", repo="cpython", token=GITHUB_TOKEN)

    # Find
    total_candidates = defaultdict(list)
    for branch in args.branches.split(","):
        print(f"\nChecking branch {branch}")
        candidates = check_prs(
            api, args.repo_path, branch, args.start, args.number, args.sort
        )
        for reason, prs in candidates.items():
            total_candidates[reason].extend(prs)

    # Report
    def report(prs: list[PR]):
        if prs:
            seen = set()
            cmd = "open "
            for pr in prs:
                if pr["number"] in seen:
                    continue
                print(f'\\[#{pr["number"]}]({pr["html_url"]}) {pr["title"]}')
                cmd += f"{pr['html_url']} "
                seen.add(pr["number"])
            print()
            print(cmd)
            if args.open_prs:
                os.system(cmd)

    print("\n[bold]Results[/bold]")
    for reason, prs in total_candidates.items():
        total = len({pr["number"] for pr in prs})
        print(f"\nFound {total} {reason}")
        report(prs)

    print("\n[bold]Summary[/bold]\n")
    for reason, prs in total_candidates.items():
        total = len({pr["number"] for pr in prs})
        print(f"* Found {total} {reason}")


if __name__ == "__main__":
    main()
