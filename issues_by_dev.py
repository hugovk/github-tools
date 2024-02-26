"""
Find number of open CPython issues per core dev.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from itertools import chain
from typing import Any, NamedTuple, TypeAlias

import requests  # pip install requests
from ghapi.all import GhApi, paged  # pip install ghapi
from prettytable import MARKDOWN, PrettyTable  # pip install prettytable
from rich import print  # pip install rich
from rich.progress import track

Issue: TypeAlias = dict[str, Any]

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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-x", "--dry-run", action="store_true", help="show but don't open issues"
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
    r = requests.get(URL)
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
    field_names = ["Author", "Issues", "PRs", "Total"]
    if args.markdown:
        table.set_style(MARKDOWN)
    elif args.links:
        table.align["Issues link"] = "l"
        table.align["PRs link"] = "l"
        field_names.extend(["Issues link", "PRs link"])
    table.field_names = field_names

    print()
    total_issues = total_prs = 0
    counter = Counter(totals)
    for author, count in counter.most_common():
        x = len(authors[author].issues)
        y = len(authors[author].prs)
        total_issues += x
        total_prs += y
        if x or y:
            match (args.markdown, args.links):
                case True, True:
                    row = (
                        author,
                        f"[{x}](https://github.com/python/cpython/issues/{author})",
                        f"[{y}](https://github.com/python/cpython/pulls/{author})",
                        x + y,
                    )
                case False, True:
                    row = (
                        author,
                        x,
                        y,
                        x + y,
                        f"https://github.com/python/cpython/issues/{author}",
                        f"https://github.com/python/cpython/pulls/{author}",
                    )
                case _:
                    row = (author, x, y, x + y)

            table.add_row(row)

    total_row = ["Total", total_issues, total_prs, total_issues + total_prs]
    if args.links and not args.markdown:
        total_row.extend(["", ""])

    table.add_row(total_row)
    print(table)


if __name__ == "__main__":
    main()
