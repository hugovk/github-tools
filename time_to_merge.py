"""
Process pr_list.jsonl created by download_pull_requests.py and
find time from open to merge in days
"""
from __future__ import annotations

import datetime as dt

import jsonlines  # pip install jsonlines

try:
    from rich import print
except ImportError:
    pass


with jsonlines.open("pr_list.jsonl") as reader:
    pull_requests = list(reader)
# print(f"Total PRs: {len(pull_requests):,}")

today = dt.datetime.today()

print("created_at, merged_at, days to merge, days since created")
for pr in reversed(pull_requests):
    if not pr["merged_at"]:
        continue
    # 2021-08-10T16:51:08Z
    timestamp_format = "%Y-%m-%dT%H:%M:%SZ"
    created_at = dt.datetime.strptime(pr["created_at"], timestamp_format)
    merged_at = dt.datetime.strptime(pr["merged_at"], timestamp_format)
    print(
        f'{pr["created_at"]}, '
        f'{pr["merged_at"]}, '
        f"{(merged_at - created_at).days}, "
        f"{(today - created_at).days}"
    )
