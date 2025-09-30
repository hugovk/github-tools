"""
Find open CPython PRs that have their linked issue closed.
They're candidates for closing.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ghapi",
#     "rich",
# ]
# ///

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from typing import Any, TypeAlias

from fastcore.net import HTTP404NotFoundError
from fastcore.xtras import obj2dict
from ghapi.all import GhApi, paged  # pip install ghapi
from rich import print  # pip install rich

Issue: TypeAlias = dict[str, Any]


GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]


def check_pr(api: GhApi, pr: Issue) -> list[Issue]:
    """
    Extract linked issue from title ("gh-XXXXXX") and check if it is closed.
    """
    gh_match = re.search(r"gh-(\d+)", pr.title, re.IGNORECASE)
    if not gh_match:
        return []
    issue_number = int(gh_match.group(1))

    try:
        issue = api.issues.get(issue_number)
    except HTTP404NotFoundError as e:
        print(f"[yellow]Error: Issue #{issue_number} not found: {e}[/yellow]")
        return []

    if issue.state == "closed":
        colour_state = "[red]closed[/red]"
        print(f"gh-{issue_number}", colour_state, issue.html_url)
        pr.setdefault("linked_issue", issue)
        print(f"[red]*** LINKED ISSUE {issue_number} IS CLOSED ***[/red]")
        return [pr]
    else:
        colour_state = f"[green]{issue.state}[/green]"
        print(f"gh-{issue_number}", colour_state, issue.html_url)

    return []


def sort_by_to_sort_and_direction(sort_by: str) -> tuple[str, str]:
    sort = "created"
    direction = "desc"
    match sort_by:
        case "newest":
            sort = "created"
            direction = "desc"
        case "oldest":
            sort = "created"
            direction = "asc"
        case "most-commented":
            sort = "comments"
            direction = "desc"
        case "least-commented":
            sort = "comments"
            direction = "asc"
        case "recently-updated":
            sort = "updated"
            direction = "desc"
        case "least-recently-updated":
            sort = "updated"
            direction = "asc"

    return sort, direction


def check_prs(
    start: int = 1,
    number: int = 100,
    author: str | None = None,
    sort_by: str = "newest",
) -> list[Issue]:
    api = GhApi(owner="python", repo="cpython", token=GITHUB_TOKEN)

    sort, direction = sort_by_to_sort_and_direction(sort_by)
    candidates = []
    pr_count = 0
    params = {
        "state": "open",
        "sort": sort,
        "direction": direction,
        "per_page": 100,
    }
    if author is not None:
        params["creator"] = author
    for page in paged(api.pulls.list, **params):
        for pr in page:
            pr_count += 1
            print(pr_count, start, number, pr.html_url)

            if pr_count < start:
                continue

            candidates.extend(check_pr(api, pr))

            if pr_count >= start + number - 1:
                return candidates

    return candidates


def save_json(data: Any, filename: str) -> None:
    # Put last_update at the start
    data = {"last_update": dt.datetime.now(dt.UTC).isoformat(), **data}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        print(f"Saved to {filename}")


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
    parser.add_argument("-j", "--json", action="store_true", help="output to JSON file")
    parser.add_argument(
        "-x", "--dry-run", action="store_true", help="show but don't open PRs"
    )
    args = parser.parse_args()

    # Find
    candidates = check_prs(args.start, args.number, args.author, args.sort)

    # Report
    print()
    print(f"Found {len(candidates)} candidates for closing")

    if candidates:
        cmd = "open "
        for pr in candidates:
            print(pr.number, pr.html_url)
            cmd += f"{pr.html_url} "
        print()
        print(cmd)
        if not args.dry_run:
            os.system(cmd)

    if args.json:
        data = {"candidates": [obj2dict(c) for c in candidates]}
        # Use same name as this .py but with .json
        filename = os.path.splitext(__file__)[0] + ".json"
        save_json(data, filename)


if __name__ == "__main__":
    main()
