#!/usr/bin/env python3
"""
Open the website for this repo (or upstream).

Tip: add to your .zshrc or similar:
alias repo=$HOME/github/github-tools/repo.py
alias upstream="repo --upstream"

Then you can do things like:
repo pulls
repo pulls/hugovk
repo pulls/@me
repo issues/hugovk
repo actions
repo branches
upstream pulls
"""
from __future__ import annotations

import argparse
import os

import git  # pip install GitPython
from termcolor import cprint  # pip install termcolor


def clean_url(url: str) -> str:
    # git@github.com:user/repo.git
    # ->
    # https://github.com/user/repo.git
    if url.startswith("git@"):
        url = "https://" + url.removeprefix("git@").replace(":", "/")

    # https://github.com/user/repo.git
    # ->
    # https://github.com:user/repo
    url = url.removesuffix(".git")

    return url


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-u",
        "--upstream",
        action="store_true",
        help="Open the upstream instead (if there is one)",
    )
    parser.add_argument(
        "tab",
        nargs="?",
        help="Open the named tab",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show but don't open webpages",
    )
    args = parser.parse_args()

    # Find the user/repo of the Git origin
    git_repo = git.Repo(".")
    url = list(git_repo.remotes.origin.urls)[0]
    if args.upstream:
        try:
            url = list(git_repo.remotes.upstream.urls)[0]
        except AttributeError:  # 'IterableList' object has no attribute 'upstream'
            cprint("No upstream, opening origin", "yellow")
    print(url)

    url = clean_url(url)

    if args.tab:
        if "gitlab" in url:
            url += "/-"
        url += "/" + args.tab

    cmd = "open " + url
    print(cmd)
    if not args.dry_run:
        os.system(cmd)


if __name__ == "__main__":
    main()


# End of file
