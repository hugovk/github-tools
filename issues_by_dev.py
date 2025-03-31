"""
Find number of open issues/PRs in the Python org team.
"""

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "ghapi",
#   "prettytable>=3.12.0",
#   "requests",
#   "rich",
# ]
# ///

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from itertools import chain
from typing import Any, NamedTuple, TypeAlias

import requests  # pip install requests
from ghapi.all import GhApi, paged  # pip install ghapi
from prettytable import PrettyTable, TableStyle  # pip install "prettytable>=3.12.0"
from rich.progress import track  # pip install rich

Issue: TypeAlias = dict[str, Any]

# Token needs read:org "Read org and team membership, read org projects"
# to read private organisation members. Otherwise only public are read.
GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]

URL = "https://raw.githubusercontent.com/python/devguide/main/core-developers/developers.csv"


class Author(NamedTuple):
    issues: list[Issue]
    prs: list[Issue]


def check_issues(author: str | None = None) -> Author:
    api = GhApi(owner="python", repo="cpython", token=GITHUB_TOKEN)

    issues = []
    prs = []
    for page in paged(
        api.issues.list_for_repo,
        state="open",
        creator=author,
        per_page=100,
    ):
        for issue in page:
            if issue.html_url.startswith("https://github.com/python/cpython/pull/"):
                prs.append(issue)
            else:
                issues.append(issue)

    return Author(issues, prs)


def markdown_link(url: str, text: str | int) -> str:
    return f"[{text}]({url})"


def terminal_link(url: str, text: str | int) -> str:
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def no_link(url: str, text: str | int) -> str:
    return str(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-m", "--markdown", action="store_true", help="Output in Markdown"
    )
    parser.add_argument("--links", action="store_true", help="Add links")
    parser.add_argument("--limit", type=int, help="Limit to this number of usernames")
    args = parser.parse_args()

    # https://docs.github.com/en/rest/orgs/members?apiVersion=2022-11-28#list-organization-members
    api = GhApi(owner="python", repo="cpython", token=GITHUB_TOKEN)
    org_members = [
        member.login
        for member in chain.from_iterable(
            paged(api.orgs.list_members, "python", per_page=100)
        )
    ]
    print(f"Found {len(org_members)} org members")

    # Download usernames CSV
    print("Download CSV")
    r = requests.get(URL, timeout=10)
    reader = csv.reader(r.text.splitlines())
    core_devs = [row[1] for row in reader if row[1]]
    print(f"Found {len(core_devs)} core devs")

    usernames = list(set(org_members) | set(core_devs))
    print(f"Found {len(usernames)} total users")

    # Find issues for each user
    authors = {}
    totals = {}
    print("Fetch issues")
    for author in track(usernames[: args.limit], description="Fetching issues..."):
        authors[author] = check_issues(author)
        totals[author] = len(authors[author].issues) + len(authors[author].prs)

    # Report
    table = PrettyTable()
    table.align = "r"
    table.align["Author"] = "l"
    field_names = ["", "Author", "Issues", "PRs", "Total"]
    if args.markdown:
        table.set_style(TableStyle.MARKDOWN)
    else:
        table.set_style(TableStyle.SINGLE_BORDER)

    table.field_names = field_names

    print()
    total_issues = total_prs = 0
    counter = Counter(totals)
    for i, (author, count) in enumerate(counter.most_common(), start=1):
        x = len(authors[author].issues)
        y = len(authors[author].prs)
        total_issues += x
        total_prs += y
        if x or y:
            match (args.markdown, args.links):
                case True, True:
                    link_function = markdown_link
                case False, True:
                    link_function = terminal_link
                case _:
                    link_function = no_link

            row = (
                i,
                author,
                link_function(f"https://github.com/python/cpython/issues/{author}", x),
                link_function(f"https://github.com/python/cpython/pulls/{author}", y),
                link_function(
                    f"https://github.com/python/cpython/issues?q=is%3Aopen+author%3A{author}",
                    x + y,
                ),
            )

            table.add_row(row)

    total_row = [
        "",
        "Total",
        f"{total_issues:,}",
        f"{total_prs:,}",
        f"{total_issues + total_prs:,}",
    ]

    table.add_row(total_row)
    print(table)


if __name__ == "__main__":
    main()
