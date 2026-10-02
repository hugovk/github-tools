"""
Find number of open issues/PRs in the Python org team.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "prettytable>=3.12.0",
#   "pygithub>=2",
#   "requests",
#   "rich",
# ]
# ///

from __future__ import annotations

import argparse
import csv
import os
from collections import Counter
from typing import NamedTuple

import requests  # pip install requests
from github.Issue import Issue  # pip install PyGitHub
from github.Repository import Repository
from prettytable import PrettyTable, TableStyle  # pip install "prettytable>=3.12.0"
from rich import print  # pip install rich
from rich.progress import track

from potential_closeable_issues import make_github, save_json

URL = "https://raw.githubusercontent.com/python/devguide/main/core-team/core-team.csv"
REPO = "https://github.com/python/cpython"


class Author(NamedTuple):
    issues: list[Issue]
    prs: list[Issue]


def check_issues(repo: Repository, author: str) -> Author:
    issues = []
    prs = []
    for issue in repo.get_issues(state="open", creator=author):
        if issue.pull_request is not None:
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
    parser.add_argument(
        "-n", "--number", type=int, help="Limit to this number of usernames"
    )
    parser.add_argument("-j", "--json", action="store_true", help="output to JSON file")
    args = parser.parse_args()

    # https://docs.github.com/en/rest/orgs/members?apiVersion=2022-11-28#list-organization-members
    # Token needs read:org "Read org and team membership, read org projects"
    # to read private organisation members. Otherwise only public are read.
    gh = make_github()
    org_members = [
        member.login for member in gh.get_organization("python").get_members()
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
    repo = gh.get_repo("python/cpython")
    authors = {}
    totals = {}
    print("Fetch issues")
    for author in track(usernames[: args.number], description="Fetching issues..."):
        authors[author] = check_issues(repo, author)
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
    data = {}
    for i, (author, count) in enumerate(counter.most_common(), start=1):
        issues = len(authors[author].issues)
        prs = len(authors[author].prs)
        total_issues += issues
        total_prs += prs
        if issues or prs:
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
                link_function(f"{REPO}/issues/{author}", issues),
                link_function(f"{REPO}/pulls/{author}", prs),
                link_function(
                    f"{REPO}/issues?q=is%3Aopen+author%3A{author}", issues + prs
                ),
            )

            table.add_row(row)
            data[author] = {"issues": issues, "prs": prs}

    total_row = [
        "",
        "Total",
        f"{total_issues:,}",
        f"{total_prs:,}",
        f"{total_issues + total_prs:,}",
    ]

    table.add_row(total_row)
    print(table)

    if args.json:
        print(data)
        # # Use same name as this .py but with .json
        filename = os.path.splitext(__file__)[0] + ".json"
        save_json(data, filename)


if __name__ == "__main__":
    main()
