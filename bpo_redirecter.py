#!/usr/bin/env python3
"""
Update BPO links to GH issues in a file or directory of files
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

import hishel  # pip install hishel
import httpx  # pip install httpx
from termcolor import colored, cprint  # pip install termcolor

try:
    from rich.logging import RichHandler  # pip install rich
except ImportError:
    RichHandler = None
    pass

# For example:
# http://bugs.python.org/issue5237
# https://bugs.python.org/issue9633
BPO_URL_REGEX = re.compile(r"https?://bugs\.python\.org/issue(\d+)")

# For example:
# :issue:`45440`
BPO_ROLE_REGEX = re.compile(r":issue:`(\d+)`")

logger = logging.getLogger(__name__)


@cache
def redirect(client: httpx.Client, bpo_number: int) -> str:
    redirect_link = f"https://bugs.python.org/issue?@action=redirect&bpo={bpo_number}"
    logger.info("Redirect link:\t%s", redirect_link)
    r = client.get(redirect_link, follow_redirects=True)
    logger.info("GitHub link:\t%s", r.url)
    return str(r.url)


def color_diff(diff: Iterable[str]) -> Iterable[str]:
    for line in diff:
        if line.startswith("+"):
            yield colored(line, "green")
        elif line.startswith("-"):
            yield colored(line, "red")
        else:
            yield line


def do_file(filename: str, dry_run: bool = False) -> None:
    with open(filename) as f:
        old_lines = f.readlines()

    new_lines = do_lines(old_lines, filename)

    if not dry_run and new_lines != old_lines:
        with open(filename, "w") as f:
            f.writelines(new_lines)


def do_lines(old_lines: list[str], filename: str) -> list[str]:
    with hishel.CacheClient() as client:
        changes = 0
        new_lines = []
        for line in old_lines:
            # print(line.strip())
            matches = 0
            ms = BPO_URL_REGEX.findall(line.strip())
            new_line = line
            for m in ms:
                logger.info("Old line:\t%s", line.rstrip())
                # bpo_link = f"https://bugs.python.org/issue{m}"
                # logger.info("BPO link:\t%s", bpo_link)
                bpo_number = int(m)
                logger.info("BPO number:\t%d", bpo_number)

                gh_link = redirect(client, bpo_number)
                new_line = BPO_URL_REGEX.sub(gh_link, new_line, count=1)
                logger.info("New line:\t%s", new_line.rstrip())

            if line != new_line:
                changes += 1
                matches += 1
                new_lines.append(new_line)

            ms = BPO_ROLE_REGEX.findall(line.strip())
            new_line = line
            for m in ms:
                logger.info("Old line:\t%s", line.rstrip())
                # bpo_role = f":issue:`{m}`"
                # logger.info("BPO link:\t%s", bpo_role)
                bpo_number = int(m)
                logger.info("BPO number:\t%d", bpo_number)

                gh_link = redirect(client, bpo_number)
                gh_number = gh_link.split("/")[-1]
                new_role = f":gh:`{gh_number}`"
                logger.info("New role:\t%s", new_role)
                new_line = BPO_ROLE_REGEX.sub(new_role, new_line, count=1)
                logger.info("New line:\t%s", new_line.rstrip())

            if line != new_line:
                changes += 1
                matches += 1
                new_lines.append(new_line)

            if matches == 0:
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

        if changes:
            return new_lines

        return old_lines


def do_file_or_path(file_or_path: str, dry_run: bool = False) -> None:
    if os.path.isfile(file_or_path):
        do_file(file_or_path, dry_run)
    else:
        for p in sorted(Path(file_or_path).rglob("*")):
            if p.suffix in (".py", ".rst", ".txt") and p.is_file():
                logger.info(p)
                do_file(str(p), dry_run)
                # print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input", help="File or directory to redirect")
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

    do_file_or_path(args.input, args.dry_run)

    logger.info(redirect.cache_info())


if __name__ == "__main__":
    sys.exit(main())
