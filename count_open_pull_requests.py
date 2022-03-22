"""
Process pr_list.jsonl created by download_pull_requests.py and
output a CSV of the number of PRs open per day
"""
import datetime as dt

import jsonlines  # pip install jsonlines

with jsonlines.open("pr_list.jsonl") as reader:
    pull_requests = [line for line in reader]
# print(f"{len(pull_requests)=}")

# Find oldest
oldest = pull_requests[0]["created_at"]
new_pull_requests = []
for pull_request in pull_requests:
    if pull_request["created_at"] < oldest:
        oldest = pull_request["created_at"]

    # Keep only the data we need to speed up later processing
    new_pull_requests.append(
        {k: v for k, v in pull_request.items() if k in ("created_at", "closed_at")}
    )
pull_requests = list(new_pull_requests)

# Find open for each day
today = dt.date.fromisoformat(oldest[:10])
end_date = dt.date.today()
delta = dt.timedelta(days=1)
while today <= end_date:
    today_str = str(today)  # yyyy-mm-dd
    open_today = 0
    new_pull_requests = []

    for pull_request in pull_requests:

        # Slice 2022-03-22T08:39:59Z into 2022-03-22
        created_date = pull_request["created_at"][:10]
        if pull_request["closed_at"]:
            closed_date = pull_request["closed_at"][:10]
        else:
            # Somewhere in the future, close enough!
            # Lets us do <= on strings instead of also checking for None
            closed_date = "9999-99-99"

        if created_date <= today_str <= closed_date:
            open_today += 1

        # Ditch closed PRs, don't need them tomorrow
        if today_str <= closed_date:
            new_pull_requests.append(pull_request)

    print(f"{today_str}, {open_today}")
    pull_requests = list(new_pull_requests)
    today += delta
