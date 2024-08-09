"""
Find closed CPython issues with open backports.
They may have been forgotten and are candidates
for merging or closing.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, TypeAlias

from ghapi.all import GhApi, paged  # pip install ghapi
from rich import print  # pip install rich

from potential_closeable_prs import sort_by_to_sort_and_direction

PR: TypeAlias = dict[str, Any]


GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]


def is_linked_issue_closed(api: GhApi, pr: PR) -> bool:
    """
    Look for a chunk like this, collect the issue:

    <!-- gh-issue-number: gh-79846 -->
    * Issue: gh-79846
    <!-- /gh-issue-number -->
    """
    if pr["base"]["ref"] == "main":
        # We only want backports
        print("  [yellow]Not a backport[/yellow]")
        return False

    if not (pr.body and "gh-issue-number" in pr.body):
        print("  [yellow]No body or linked issue[/yellow]")
        return False

    linked_issue = None
    for line in pr.body.splitlines():
        if line.startswith("<!-- gh-issue-number: gh-"):
            linked_issue = line.removeprefix("<!-- gh-issue-number: gh-").removesuffix(
                " -->"
            )
            break

    if not linked_issue:
        print("  [yellow]No linked issue found[/yellow]")
        return False

    issue = api.issues.get(linked_issue)

    colour_state = (
        "[green]open[/green]" if issue["state"] == "open" else "[red]closed[/red]"
    )
    print("  gh-" + linked_issue, colour_state, issue.html_url)
    return issue["state"] == "closed"


def check_prs(
    start: int = 1,
    number: int = 100,
    author: str | None = None,
    sort_by: str = "newest",
) -> list[PR]:
    api = GhApi(owner="python", repo="cpython", token=GITHUB_TOKEN)

    sort, direction = sort_by_to_sort_and_direction(sort_by)

    candidates = []
    pr_count = 0
    for page in paged(
        api.pulls.list,
        state="open",
        creator=author,
        sort=sort,
        direction=direction,
        per_page=100,
    ):
        for pr in page:
            pr_count += 1
            print(pr_count, start, number, pr.html_url)

            if pr_count < start:
                continue

            if is_linked_issue_closed(api, pr):
                candidates.append(pr)

            if pr_count >= start + number - 1:
                return candidates

    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-s", "--start", default=1, type=int, help="start at this PR number"
    )
    parser.add_argument(
        "-n", "--number", default=100, type=int, help="number of PRs to check"
    )
    parser.add_argument("-a", "--author", help="PR author, blank for any")
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
        "-x", "--dry-run", action="store_true", help="show but don't open PRs"
    )
    args = parser.parse_args()

    # Find
    candidates = check_prs(args.start, args.number, args.author, args.sort)

    # Report
    print()
    print(f"Found {len(candidates)} orphaned backports (parent issue closed)")

    if candidates:
        cmd = "open "
        for pr in candidates:
            print(f'\\[#{pr["number"]}]({pr["html_url"]}) {pr["title"]}')
            cmd += f"{pr['html_url']} "
        print()
        print(cmd)
        if not args.dry_run:
            os.system(cmd)


if __name__ == "__main__":
    main()
