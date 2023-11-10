"""
Downloads data for all issues or PRs from a repo and saves them in JSON Lines files
https://jsonlines.org

Thanks to Ammar Askar
https://discuss.python.org/t/decision-needed-should-we-close-stale-prs-and-how-many-lapsed-days-are-prs-considered-stale/4637/11?u=hugovk
"""
from __future__ import annotations

import argparse
import json
import os

from github import Github  # pip install PyGithub

GITHUB_TOKEN = os.environ["GITHUB_TOOLS_TOKEN"]
OUTPUT_FILE_ISSUES = "issue_list.jsonl"
OUTPUT_FILE_PRS = "pr_list.jsonl"


def download(label: str, output_file: str, repo_get_fn) -> None:
    # Output file is 514 MB for 31,984 PRs!
    # Output file is 525 MB for 32,611 PRs! (16 mins)
    # Output file is 387 MB for 91,726 issues! (16 mins)
    with open(output_file, "w", encoding="utf-8") as f:
        for i, item in enumerate(repo_get_fn(state="all")):
            if i % 10 == 0:
                print(f"Retrieved {i} {label}", end="\r")
            f.write(json.dumps(item._rawData))
            f.write("\n")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i",
        "--issues",
        action="store_true",
        help="Download issues only. If neither flag set, download PRs and issues.",
    )
    parser.add_argument(
        "-p",
        "--prs",
        action="store_true",
        help="Download PRs only. If neither flag used, download PRs and issues.",
    )
    args = parser.parse_args()

    # If neither flag, download both sets
    if not args.issues and not args.prs:
        args.issues = args.prs = True

    g = Github(GITHUB_TOKEN, per_page=100)
    repo = g.get_repo("python/cpython")

    if args.prs:
        print("Downloading PRs")
        download("PRs", OUTPUT_FILE_PRS, repo.get_pulls)

    if args.issues:
        print("Downloading issues")
        download("issues", OUTPUT_FILE_ISSUES, repo.get_issues)


if __name__ == "__main__":
    main()
