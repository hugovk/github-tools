"""
Downloads data for all PRs from a repo and saves in a JSON Lines file
https://jsonlines.org

Thanks to Ammar Askar
https://discuss.python.org/t/decision-needed-should-we-close-stale-prs-and-how-many-lapsed-days-are-prs-considered-stale/4637/11?u=hugovk
"""
import json
import os

from github import Github

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

g = Github(GITHUB_TOKEN, per_page=100)

# Output file is 514 MB for 31,984 PRs!
with open("pr_list.jsonl", "w", encoding="utf-8") as f:
    repo = g.get_repo("python/cpython")

    for i, pull in enumerate(repo.get_pulls("all")):
        print(f"Retrieved {i} pull requests")
        f.write(json.dumps(pull._rawData))
        f.write("\n")
