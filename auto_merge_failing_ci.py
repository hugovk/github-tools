"""
Find CPython PRs with auto-merge enabled but failing CI.
They won't be merged until the CI is fixed or re-run.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ghapi<2",
#     "rich",
#     "stamina",
# ]
# ///

from __future__ import annotations

import argparse
import os
import urllib
from typing import Any, TypeAlias

import stamina
from fastcore.xtras import obj2dict
from ghapi.all import GhApi, paged  # pip install ghapi
from rich import print  # pip install rich

from potential_closeable_issues import save_json, sort_by_to_sort_and_direction

PR: TypeAlias = dict[str, Any]


GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]

FAILING_CONCLUSIONS = ("failure", "timed_out")
FAILING_STATES = ("failure", "error")

# Aggregate check that just mirrors the other checks
IGNORED_CHECKS = ("All required checks pass",)


def get_failing_checks(api: GhApi, pr: PR) -> list[str]:
    """Names of failing check runs and commit statuses for the PR's head commit."""
    sha = pr["head"]["sha"]
    failing = set()

    check_runs = api.checks.list_for_ref(sha, per_page=100)
    for run in check_runs["check_runs"]:
        if (
            run["conclusion"] in FAILING_CONCLUSIONS
            and run["name"] not in IGNORED_CHECKS
        ):
            failing.add(run["name"])

    combined = api.repos.get_combined_status_for_ref(sha, per_page=100)
    for status in combined["statuses"]:
        if status["state"] in FAILING_STATES:
            failing.add(status["context"])

    return sorted(failing)


@stamina.retry(on=urllib.error.HTTPError)
def stamina_paged(*args, **kwargs):
    return paged(*args, **kwargs)


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

    for page in stamina_paged(
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

            if pr.auto_merge:
                failing_checks = get_failing_checks(api, pr)
                if failing_checks:
                    print("  [red]" + ", ".join(failing_checks) + "[/red]")
                    candidate = obj2dict(pr)
                    candidate["failing_checks"] = failing_checks
                    candidates.append(candidate)
                else:
                    print("  [green]CI not failing[/green]")
            else:
                print("  [yellow]Auto-merge not enabled[/yellow]")

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
    parser.add_argument("-j", "--json", action="store_true", help="output to JSON file")
    parser.add_argument(
        "-x", "--dry-run", action="store_true", help="show but don't open PRs"
    )
    args = parser.parse_args()

    # Find
    candidates = check_prs(args.start, args.number, args.author, args.sort)

    # Report
    print("\n[bold]Summary")
    print(f"Found {len(candidates)} auto-merge PRs with failing CI")

    if candidates:
        cmd = "open "
        for pr in candidates:
            print(f'\\[#{pr["number"]}]({pr["html_url"]}) {pr["title"]}')
            cmd += f"{pr['html_url']} "
        print()
        print(cmd)
        if not args.dry_run:
            os.system(cmd)

    if args.json:
        data = {"candidates": candidates}
        # Use same name as this .py but with .json
        filename = os.path.splitext(__file__)[0] + ".json"
        save_json(data, filename)


if __name__ == "__main__":
    main()
