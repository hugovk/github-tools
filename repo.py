#!/usr/bin/env python3
"""
Open the website for this repo (or upstream).
"""
from __future__ import annotations

import argparse
import os

import git  # pip install GitPython
from termcolor import cprint  # pip install termcolor


# From https://peps.python.org/pep-0616/#specification
def removeprefix(self: str, prefix: str) -> str:
    if self.startswith(prefix):
        return self[len(prefix) :]
    else:
        return self[:]


def removesuffix(self: str, suffix: str) -> str:
    # suffix='' should not call self[:-0].
    if suffix and self.endswith(suffix):
        return self[: -len(suffix)]
    else:
        return self[:]


def main(args):
    # Find the user/repo of the Git origin
    git_repo = git.Repo(".")
    url = list(git_repo.remotes.origin.urls)[0]
    if args.upstream:
        try:
            url = list(git_repo.remotes.upstream.urls)[0]
        except AttributeError:  # 'IterableList' object has no attribute 'upstream'
            cprint("No upstream, opening origin", "yellow")
    print(url)

    # git@github.com:user/repo.git
    # ->
    # https://github.com/user/repo.git
    if url.startswith("git@"):
        url = "https://" + removeprefix(url, "git@").replace(":", "/")

    # https://github.com/user/repo.git
    # ->
    # https://github.com:user/repo
    url = removesuffix(url, ".git")

    if args.tab:
        if "gitlab" in url:
            url += "/-"
        url += "/" + args.tab

    cmd = "open " + url
    print(cmd)
    if not args.dry_run:
        os.system(cmd)


if __name__ == "__main__":
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
    main(args)


# End of file
