"""
Find open CPython issues that have their linked PRs merged.
They're candidates for closing.
"""
from __future__ import annotations

import argparse
import os

from github import Github  # pip install PyGithub
from rich import print  # pip install rich

GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]


def check_issues(start: int = 1, number: int = 100, dry_run: bool = False) -> None:
    g = Github(GITHUB_TOKEN, per_page=100)
    repo = g.get_repo("python/cpython")

    candidates = []
    issue_count = 0
    for i, issue in enumerate(repo.get_issues(state="open")):
        if issue.html_url.startswith("https://github.com/python/cpython/pull/"):
            continue

        issue_count += 1
        print(issue_count, start, number, issue.html_url)

        if issue_count < start:
            continue

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

        if "gh-linked-prs" in issue.body:
            in_linked_prs_section = False
            linked_prs = []
            states = []
            for line in issue.body.splitlines():
                if line.strip() == "<!-- gh-linked-prs -->":
                    in_linked_prs_section = True
                elif (
                    in_linked_prs_section and line.strip() == "<!-- /gh-linked-prs -->"
                ):
                    in_linked_prs_section = False
                elif in_linked_prs_section and line.startswith("* gh-"):
                    linked_prs.append(line.strip())

            for pr_line in linked_prs:
                pr_number = int(pr_line.split("-")[1])
                pr = repo.get_pull(pr_number)

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

            if all(state == "closed" for state in states):
                print("[red]*** ALL PRS CLOSED ***[/red]")
                candidates.append(issue)
            elif all(state == "merged" for state in states):
                print("[purple]*** ALL PRS MERGED ***[/purple]")
                candidates.append(issue)
            elif all(state in ("closed", "merged") for state in states):
                print("*** ALL PRS [red]CLOSED[/red] OR [purple]MERGED[/purple] ***")
                candidates.append(issue)

        if issue_count >= start + number - 1:
            break

    print()
    print(f"Found {len(candidates)} candidates for closing")
    cmd = "open "
    for issue in candidates:
        print(issue.number, issue.html_url)
        cmd += f"{issue.html_url} "
    print()
    print(cmd)
    if not dry_run:
        os.system(cmd)


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
    parser.add_argument(
        "-x", "--dry-run", action="store_true", help="Show but don't open issues"
    )
    args = parser.parse_args()

    check_issues(args.start, args.number, args.dry_run)


if __name__ == "__main__":
    main()
