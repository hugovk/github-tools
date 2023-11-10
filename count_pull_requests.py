"""
Process pr_list.jsonl created by download_pull_requests.py and
output a CSV of the number of PRs open per day
"""
from __future__ import annotations

import argparse
import datetime as dt
from collections import defaultdict

import jsonlines  # pip install jsonlines


def find_oldest(pull_requests: list[dict]) -> tuple[list[dict], str]:
    # Find oldest
    oldest = pull_requests[0]["created_at"]
    new_pull_requests = []
    for pr in pull_requests:
        if pr["created_at"] < oldest:
            oldest = pr["created_at"]

        # Keep only the data we need to speed up later processing
        new_pull_requests.append(
            {
                k: v
                for k, v in pr.items()
                if k in ("created_at", "closed_at", "merged_at")
            }
        )
    pull_requests = list(new_pull_requests)
    return pull_requests, oldest


def open_per_day(pull_requests: list[dict], oldest: str) -> None:
    """
    Find the total number of open pull requests per day
    """
    today = dt.date.fromisoformat(oldest[:10])
    end_date = dt.date.today()
    delta = dt.timedelta(days=1)
    while today <= end_date:
        today_str = str(today)  # yyyy-mm-dd
        open_today = 0
        new_pull_requests = []

        for pr in pull_requests:
            # Slice 2022-03-22T08:39:59Z into 2022-03-22
            created_date = pr["created_at"][:10]
            if pr["closed_at"]:
                closed_date = pr["closed_at"][:10]
            else:
                # Somewhere in the future, close enough!
                # Lets us do <= on strings instead of also checking for None
                closed_date = "9999-99-99"

            if created_date <= today_str <= closed_date:
                open_today += 1

            # Ditch closed PRs, don't need them tomorrow
            if today_str <= closed_date:
                new_pull_requests.append(pr)

        print(f"{today_str}, {open_today}")
        pull_requests = list(new_pull_requests)
        today += delta


def opened_per_week(pull_requests: list[dict]) -> None:
    """
    Find the number of pull requests opened in each week
    """
    open_by_week = defaultdict(lambda: defaultdict(int))
    for pr in pull_requests:
        # Slice 2022-03-22T08:39:59Z into 2022-03-22 and make dt.date
        created_date = dt.date.fromisoformat(pr["created_at"][:10])
        week_str = (
            f"{created_date.isocalendar().year} "
            f"w{created_date.isocalendar().week:02}"
        )

        # Count all
        open_by_week[week_str]["any state"] += 1

        # Count only those still open today, they have no closed_at date
        if not pr["closed_at"]:
            open_by_week[week_str]["still open"] += 1
            # open_by_week[week_str] += 1

    print("Week number, PRs opened this week, PRs opened this week and still open")
    for k, v in sorted(open_by_week.items()):
        print(f"{k}, {v['any state']}, {v['still open']}")


def closed_per_week(pull_requests: list[dict]) -> None:
    """
    Find the number of pull requests closed in each week
    """
    closed_by_week = defaultdict(lambda: defaultdict(int))
    for pr in pull_requests:
        if not pr["closed_at"]:
            continue
        # Slice 2022-03-22T08:39:59Z into 2022-03-22 and make dt.date
        closed_date = dt.date.fromisoformat(pr["closed_at"][:10])
        week_str = (
            f"{closed_date.isocalendar().year} w{closed_date.isocalendar().week:02}"
        )

        # Count all
        closed_by_week[week_str]["closed"] += 1

        # Count only those that got merged
        if pr["merged_at"]:
            closed_by_week[week_str]["merged"] += 1
            # open_by_week[week_str] += 1

    print("Week number, PRs closed this week, PRs merged this week")
    for k, v in sorted(closed_by_week.items()):
        # print(f"{k}, {v}")
        print(f"{k}, {v['closed']}, {v['merged']}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--open_per_day", action="store_true", help=open_per_day.__doc__
    )
    parser.add_argument(
        "--opened_per_week", action="store_true", help=opened_per_week.__doc__
    )
    parser.add_argument(
        "--closed_per_week", action="store_true", help=closed_per_week.__doc__
    )
    args = parser.parse_args()

    with jsonlines.open("pr_list.jsonl") as reader:
        pull_requests = [line for line in reader]
    # print(f"{len(pull_requests)=}")

    pull_requests, oldest = find_oldest(pull_requests)
    if args.open_per_day:
        open_per_day(pull_requests, oldest)
    if args.opened_per_week:
        opened_per_week(pull_requests)
    if args.closed_per_week:
        closed_per_week(pull_requests)


if __name__ == "__main__":
    main()
