#!/usr/bin/env python
# encoding: utf-8
"""
Download all the diffs of PRs made during Hacktoberfest
You can then run `diffstat /tmp/hacktoberfest/*.diff` to get a summary:
    714 files changed, 9843 insertions(+), 13719 deletions(-)
"""
from __future__ import print_function, unicode_literals

import argparse
import datetime
import os
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
    pprint(r)

    try:
        next_url = r.links["next"]["url"]
    except KeyError:
        next_url = None

    if int(r.headers['X-Ratelimit-Remaining']) < 12:
        print("r.status_code", r.status_code)
        print("X-Ratelimit-Limit", r.headers['X-Ratelimit-Limit'])
        print("X-Ratelimit-Remaining", r.headers['X-Ratelimit-Remaining'])
        print("X-RateLimit-Reset", r.headers['X-RateLimit-Reset'])
        remaining_time = int(r.headers['X-RateLimit-Reset']) - time.time()
        print(remaining_time, "seconds")
        print(remaining_time/60, "minutes")
        reset_time = datetime.datetime.fromtimestamp(
                        int(int(r.headers['X-RateLimit-Reset']))
                    ).strftime('%Y-%m-%d %H:%M:%S')
        print(reset_time)

    if r.status_code == 200:
        return r.json(), next_url

    elif r.status_code == 403:
        if int(r.headers['X-Ratelimit-Remaining']) == 0:
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

        issues.extend(new_issues)

        for issue in issues:
            download_diff(issue)

        if not next_url:
            break

    return issues


def download_diff(issue):
    # pprint(issue)
    print("{}\t{}".format(issue["html_url"], issue["title"]))
    repository_url = issue["repository_url"]
    org = repository_url.split("/")[-2]
    repo = repository_url.split("/")[-1]
    outfile = "{}-{}-{}.diff".format(org, repo, issue["number"])
    outfile = os.path.join("/tmp/hacktoberfest/", outfile)
    # print(outfile)

    cmd = "wget --quiet -nc {} -O {}".format(issue["pull_request"]["diff_url"],
                                             outfile)
    # print(cmd)
    os.system(cmd)


def mkdir(directory):
    import os
    if not os.path.isdir(directory):
        os.mkdir(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download all the diffs of PRs made during Hacktoberfest",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-a', '--author', default='hugovk',
        help="Find PRs created by this user")
    parser.add_argument(
        '-y', '--year', default='2018',
        help="Find PRs in October of this year")
    parser.add_argument(
        '-t', '--type', default='all',
        choices=('all', 'open', 'merged', 'unmerged'),
        help="Filter by state of PR")
    args = parser.parse_args()

    # is:pr author:hugovk created:2017-10-01..2017-10-31 is:open
    # is:pr author:hugovk created:2017-10-01..2017-10-31 is:closed is:merged
    # is:pr author:hugovk created:2017-10-01..2017-10-31 is:closed is:unmerged

    # https://developer.github.com/v3/search/#search-issues

    start_url = ('https://api.github.com/search/issues?q=is:pr+author:{author}'
                 '+created:{year}-09-30..{year}-11-01+{type}')

    pr_type = ""
    if args.type == "open":
        pr_type = "is:open"
    elif args.type == "merged":
        pr_type = "is:closed+is:merged"
    elif args.type == "unmerged":
        pr_type = "is:closed+is:unmerged"

    mkdir("/tmp/hacktoberfest/")
    prs = get_prs(start_url.format(author=args.author,
                                   type=pr_type,
                                   year=args.year))

    print_type = "" if args.type == "all" else args.type + " "
    print("{} total {}PRs".format(len(prs), print_type))

# End of file
