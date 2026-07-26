"""
Find open CPython issues that have their linked PRs merged.
They're candidates for closing.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pygithub>=2",
#     "rich",
# ]
# ///

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
from typing import Any, TypeAlias

from github import Auth, Github, UnknownObjectException  # pip install PyGitHub
from github.GithubRetry import GithubRetry
from github.Issue import Issue
from github.Repository import Repository
from rich import print  # pip install rich

IssueData: TypeAlias = dict[str, Any]


logging.basicConfig()
# Show GithubRetry's rate-limit waits in the CI log
logging.getLogger("github").setLevel(logging.INFO)

GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]


def make_github() -> Github:
    """Client that sleeps out rate limits and retries transient errors.

    GithubRetry itself handles 403, sleeping until the rate limit resets,
    and appends it to status_forcelist. As well as server errors, retry 401:
    GitHub intermittently rejects a valid token with "Bad credentials" at a
    random point in a long request stream; it succeeds on resend.
    """
    retry = GithubRetry(
        backoff_factor=2,
        status_forcelist=[401, 429, *range(500, 600)],
    )
    return Github(auth=Auth.Token(GITHUB_TOKEN), per_page=100, retry=retry)


def check_issue(repo: Repository, issue: Issue) -> list[IssueData]:
    """
    Look for a chunk like this, collect the PRs:

    <!-- gh-linked-prs -->
    ### Linked PRs
    * gh-111091
    * gh-111106
    * gh-111121
    * gh-111122
    * gh-111585
    * gh-111587
    * gh-111620
    * gh-111672
    * gh-111688
    <!-- /gh-linked-prs -->
    """
    candidates = []
    if not (issue.body and "gh-linked-prs" in issue.body):
        return []

    in_linked_prs_section = False
    linked_prs = []
    linked_pr_data = []
    states = []
    for line in issue.body.splitlines():
        if line.strip() == "<!-- gh-linked-prs -->":
            in_linked_prs_section = True
        elif in_linked_prs_section and line.strip() == "<!-- /gh-linked-prs -->":
            in_linked_prs_section = False
        elif in_linked_prs_section and line.startswith("* gh-"):
            linked_prs.append(line.strip())

    for pr_line in linked_prs:
        # pr_line is usually like "* gh-12345" but sometimes extra text is added
        # like "* gh-12345 (abandoned proposal)", so extract the gh-12345 part
        word = next(word for word in pr_line.split() if word.startswith("gh-"))
        pr_number = int(word.split("-")[1])
        try:
            pr = repo.get_pull(pr_number)
        except UnknownObjectException as e:
            print(f"[yellow]PR {pr_number} not found: {e}[/yellow]")
            continue

        if pr.merged:
            states.append("merged")
        else:
            states.append(pr.state)

        if pr.merged:
            colour_state = "[purple]merged[/purple]"
        elif pr.state == "open":
            colour_state = f"[green]{pr.state}[/green]"
        elif pr.state == "closed":
            colour_state = f"[red]{pr.state}[/red]"
        else:
            colour_state = pr.state
        print(pr_line, colour_state, pr.html_url)

        # Merge in the linked PR data to the issue
        linked_pr_data.append(pr.raw_data)

    issue_data = issue.raw_data | {"linked_prs": linked_pr_data}
    if not states:
        print("[yellow]*** NO PRS FOUND ***[/yellow]")
    elif all(state == "closed" for state in states):
        print("[red]*** ALL PRS CLOSED ***[/red]")
        candidates.append(issue_data)
    elif all(state == "merged" for state in states):
        print("[purple]*** ALL PRS MERGED ***[/purple]")
        candidates.append(issue_data)
    elif all(state in ("closed", "merged") for state in states):
        print("*** ALL PRS [red]CLOSED[/red] OR [purple]MERGED[/purple] ***")
        candidates.append(issue_data)

    return candidates


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


def check_issues(
    start: int = 1,
    number: int = 100,
    author: str | None = None,
    sort_by: str = "newest",
) -> list[IssueData]:
    repo = make_github().get_repo("python/cpython")

    sort, direction = sort_by_to_sort_and_direction(sort_by)
    candidates = []
    issue_count = 0
    params = {
        "state": "open",
        "sort": sort,
        "direction": direction,
    }
    if author is not None:
        params["creator"] = author
    for issue in repo.get_issues(**params):
        if issue.pull_request is not None:
            continue

        issue_count += 1
        print(issue_count, start, number, issue.html_url)

        if issue_count < start:
            continue

        candidates.extend(check_issue(repo, issue))

        if issue_count >= start + number - 1:
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
        "-s", "--start", default=1, type=int, help="start at this issue number"
    )
    parser.add_argument(
        "-n", "--number", default=100, type=int, help="number of issues to check"
    )
    parser.add_argument("-a", "--author", help="issue author, blank for any")
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
        "-x", "--dry-run", action="store_true", help="show but don't open issues"
    )
    args = parser.parse_args()

    # Find
    candidates = check_issues(args.start, args.number, args.author, args.sort)

    # Report
    print()
    print(f"Found {len(candidates)} candidates for closing")

    if candidates:
        cmd = "open "
        for issue in candidates:
            print(issue["number"], issue["html_url"])
            cmd += f"{issue['html_url']} "
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
