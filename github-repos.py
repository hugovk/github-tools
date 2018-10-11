#!/usr/bin/env python
# encoding: utf-8
"""
Show which non-fork repos I created this year.
"""
from __future__ import print_function

import argparse
import datetime

import requests

# from pprint import pprint

REPOS_URL = "https://api.github.com/users/{0}/repos?type=owner&per_page=100"


# cmd.exe cannot do Unicode so encode first
def print_it(text):
    print(text.encode("utf-8"))


def timestamp():
    """ Print a timestamp and the filename with path """
    print(datetime.datetime.now().strftime("%A, %d. %B %Y %I:%M%p") + " " + __file__)


def bleep(url):
    """Call the API and return JSON and next URL"""
    print(url)
    r = requests.get(url)

    try:
        next = r.links["next"]["url"]
    except KeyError:
        next = None

    print("r.status_code", r.status_code)
    print("X-Ratelimit-Limit", r.headers["X-Ratelimit-Limit"])
    print("X-Ratelimit-Remaining", r.headers["X-Ratelimit-Remaining"])

    if (r.status_code) == 200:
        return r.json(), next

    return None, None


def bloop(user, url):
    """Get all JSON from each page of API results"""
    results = []

    # Fetch all from GitHub
    next_page = REPOS_URL.format(user)
    while True:
        new_results, next_page = bleep(next_page)
        results.extend(new_results)
        print(len(results))

        if not next_page:
            break

    return results


def get_repos(user, year):
    """Get all non-fork repos created in this year"""
    repos = bloop(user, REPOS_URL)
    #     pprint(repos)
    print(len(repos))

    kept = []
    # forks_count = 0
    # stargazers_count = 0
    # watchers_count = 0
    # open_issues_count = 0
    # subscribers_count = 0
    for repo in repos:
        if not repo["fork"] and repo["created_at"].startswith(str(year)):
            kept.append(repo)
            # forks_count += repo["forks_count"]
            # stargazers_count += repo["stargazers_count"]
            # watchers_count += repo["watchers_count"]
            # open_issues_count += repo["open_issues_count"]
            # subscribers_count += repo["subscribers_count"]
            print(repo["html_url"])

    print(len(kept), "non-fork repos created in", year)

    # print("forks_count", forks_count)
    # print("stargazers_count", stargazers_count)
    # print("watchers_count", watchers_count)
    # print("open_issues_count", open_issues_count)
    # print("subscribers_count", subscribers_count)


if __name__ == "__main__":

    timestamp()

    parser = argparse.ArgumentParser(
        description="Show which non-fork repos I created this year.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--user", default="hugovk", help="User to check")
    parser.add_argument("--year", default="2015", help="Year to check")
    args = parser.parse_args()

    get_repos(args.user, args.year)

# End of file
