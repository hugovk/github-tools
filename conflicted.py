#!/usr/bin/env python
# encoding: utf-8
"""
Find which of my PRs have merge conflicts.
"""
from __future__ import print_function, unicode_literals

import argparse
import datetime
import sys
import time
from pprint import pprint

import requests


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def bleep(url):
    """ Call the API and return JSON and next URL """
    # print(url)
    r = requests.get(url)
    # pprint(r)

    try:
        next_url = r.links["next"]["url"]
    except KeyError:
        next_url = None

    if int(r.headers["X-Ratelimit-Remaining"]) < 12:
        print("r.status_code", r.status_code)
        print("X-Ratelimit-Limit", r.headers["X-Ratelimit-Limit"])
        print("X-Ratelimit-Remaining", r.headers["X-Ratelimit-Remaining"])
        print("X-RateLimit-Reset", r.headers["X-RateLimit-Reset"])
        remaining_time = int(r.headers["X-RateLimit-Reset"]) - time.time()
        print(remaining_time, "seconds")
        print(remaining_time / 60, "minutes")
        reset_time = datetime.datetime.fromtimestamp(
            int(int(r.headers["X-RateLimit-Reset"]))
        ).strftime("%Y-%m-%d %H:%M:%S")
        print(reset_time)

    if r.status_code == 200:
        return r.json(), next_url

    elif r.status_code == 403:
        if int(r.headers["X-Ratelimit-Remaining"]) == 0:
            eprint("Rate limit exceeded")
        sys.exit(403)

    return None, None


def get_prs(start_url):
    issues = []

    # Fetch all issues from GitHub
    next_url = start_url
    while True:
        data, next_url = bleep(next_url)
        new_issues = data["items"]
        print("total_count", data["total_count"])

        for issue in new_issues:
            # pprint(issue)
            pr_url = issue["pull_request"]["url"]

            pr_data, _ = bleep(pr_url)
            # pprint(pr_data)
            if pr_data["mergeable"]:
                # print("mergeable:\t{}".format(issue["html_url"]))
                pass
            else:
                print("unmergeable:\t{}".format(issue["html_url"]))
                issues.append(issue)

        if not next_url:
            break

    return issues


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find which of my PRs have merge conflicts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-a", "--author", default="hugovk", help="Find PRs created by this user"
    )
    args = parser.parse_args()

    # https://developer.github.com/v3/search/#search-issues

    start_url = (
        "https://api.github.com/search/issues?q=is:pr+author:{author}"
        "+sort:updated-asc+is:open".format(author=args.author)
    )
    print(start_url)

    prs = get_prs(start_url)
    pprint(prs)

    print("{} total unmergeable PRs".format(len(prs)))

# End of file
