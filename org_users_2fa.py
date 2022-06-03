"""
List users in an org with 2FA disabled
"""
import os

from github import Github
from termcolor import cprint

GITHUB_TOKEN = os.environ["GITHUB_TOOLS_REPO_TOKEN"]

g = Github(GITHUB_TOKEN, per_page=100)
org = g.get_organization("digiaonline")
all_results = []


def summarise(all_: list, disabled: list) -> tuple[int, int, str, int, str]:
    number = len(all_)
    print()

    number_disabled = len(disabled)
    number_enabled = number - number_disabled
    percent_enabled = f"{number_enabled / number:.0%}"
    percent_disabled = f"{number_disabled / number:.0%}"
    cprint(
        f"2FA enabled:  {number_enabled} / {number} ({percent_enabled})",
        "green",
    )
    cprint(
        f"2FA disabled: {number_disabled} / {number} ({percent_disabled})",
        "red",
    )
    print()

    for user in disabled:
        print(
            f"{user.login}"
            f"\t{user.name if user.name else ''}"
            f"\t{user.company if user.company else ''}"
        )
    print()
    return (
        number,
        number_enabled,
        percent_enabled,
        number_disabled,
        percent_disabled,
    )


print()
cprint("MEMBERS", attrs=["bold"])

members = list(org.get_members())
members_disabled = list(org.get_members("2fa_disabled"))

results = summarise(members, members_disabled)
all_results.extend(results)

cprint("COLLABORATORS", attrs=["bold"])

collaborators = list(org.get_outside_collaborators())
collaborators_disabled = list(org.get_outside_collaborators("2fa_disabled"))

results = summarise(collaborators, collaborators_disabled)
all_results.extend(results)

cprint("COMBINED", attrs=["bold"])

combined = members + collaborators
combined_disabled = members_disabled + collaborators_disabled

# Sort by login
combined_disabled = sorted(combined_disabled, key=lambda user: user.login.lower())

results = summarise(combined, combined_disabled)
all_results.extend(results)

print(*all_results, sep="\t")
