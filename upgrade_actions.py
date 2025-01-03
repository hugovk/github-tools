#!/usr/bin/env python3
"""
Upgrade GitHub Actions versions in workflow file or directory
"""
from __future__ import annotations

import argparse
import difflib
import logging
import os
import re
import sys
from collections.abc import Iterable
from functools import cache
from pathlib import Path

import feedparser  # pip install feedparser
from termcolor import colored, cprint

try:
    from rich.logging import RichHandler
except ImportError:
    RichHandler = None
    pass

USES_REGEX = re.compile(r"(- )?uses: \"?([a-z-]+/[a-z-]+)@([a-z0-9.]+)\"?")


@cache
def get_repo_tags(repo: str) -> Iterable[str]:
    url = f"https://github.com/{repo}/tags.atom"
    logging.info(url)
    feed = feedparser.parse(url)
    return [entry.link.split("/")[-1] for entry in feed.entries]


@cache
def update_tag(repo: str, old_version: str) -> str:
    if old_version in ("main", "master"):
        return old_version
    tags = get_repo_tags(repo)
    logging.info(tags)
    same_length_tags = [tag for tag in tags if len(tag) == len(old_version)]
    logging.info(same_length_tags)
    same_length_tags.sort(reverse=True)
    logging.info(same_length_tags)
    try:
        tag = same_length_tags[0]
    except IndexError:
        cprint(
            f"No upgrade found for https://github.com/{repo}\n"
            f"  Old version: {old_version}\n"
            f"  New tags: {tags}",
            "red",
        )
        tag = None
    return tag


def color_diff(diff: Iterable[str]) -> Iterable[str]:
    for line in diff:
        if line.startswith("+"):
            yield colored(line, "green")
        elif line.startswith("-"):
            yield colored(line, "red")
        else:
            yield line


def do_file(filename: str, dry_run: bool) -> None:
    with open(filename) as f:
        old_lines = f.readlines()

    changes = 0
    new_lines = []
    for line in old_lines:
        m = USES_REGEX.search(line.strip())
        if m:
            repo = m[2]
            version = m[3]
            if repo == "pypa/gh-action-pypi-publish" and version == "release":
                new_lines.append(line)
                logging.info("%s's '%s' is a branch not tag, skipping", repo, version)
                continue
            new_version = update_tag(repo, version)
            if new_version and version != new_version:
                changes += 1
                new_line = line.replace(f"{repo}@{version}", f"{repo}@{new_version}")
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if changes:
        diff = color_diff(
            difflib.unified_diff(
                old_lines, new_lines, fromfile=filename, tofile=filename
            )
        )
        print("".join(diff))
    else:
        cprint(f"no change for {filename}", "yellow")

    if changes and not dry_run:
        with open(filename, "w") as f:
            f.writelines(new_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        default=".github/workflows/",
        nargs="?",
        help="Workflow file or directory to upgrade",
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Show but don't save changes"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
        default=logging.WARNING,
        help="Print extra messages to stderr",
    )
    args = parser.parse_args()
    if RichHandler:
        logging.basicConfig(
            level=args.loglevel, format="%(message)s", handlers=[RichHandler()]
        )
    else:
        logging.basicConfig(level=args.loglevel, format="%(message)s")

    if os.path.isfile(args.input):
        do_file(args.input, args.dry_run)
    else:
        for path in Path(args.input).rglob("*.y*ml"):
            logging.info(path)
            do_file(str(path), args.dry_run)
            print()

    logging.info("update_tag:\t%s", update_tag.cache_info())
    logging.info("get_repo_tags:\t%s", get_repo_tags.cache_info())


if __name__ == "__main__":
    sys.exit(main())
