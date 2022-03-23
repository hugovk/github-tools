"""
Process pr_list.jsonl created by download_pull_requests.py and
output a CSV of the number of PRs open per day
"""
import datetime as dt

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
            {k: v for k, v in pr.items() if k in ("created_at", "closed_at")}
        )
    pull_requests = list(new_pull_requests)
    return pull_requests, oldest


def open_per_day(pull_requests: list[dict], oldest: str):
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


def main():
    with jsonlines.open("pr_list.jsonl") as reader:
        pull_requests = [line for line in reader]
    # print(f"{len(pull_requests)=}")

    pull_requests, oldest = find_oldest(pull_requests)
    open_per_day(pull_requests, oldest)


if __name__ == "__main__":
    main()
