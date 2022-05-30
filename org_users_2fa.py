"""
List users in an org with 2FA disabled
"""
import os

from github import Github
from termcolor import cprint

GITHUB_TOKEN = os.environ["GITHUB_TOOLS_REPO_TOKEN"]

g = Github(GITHUB_TOKEN, per_page=100)
org = g.get_organization("digiaonline")


def summarise(all_: list, disabled_2fa: list) -> None:
    number = len(all_)
    print("All:", number)
    print()

    number_disabled_2fa = len(disabled_2fa)
    number_enabled_2fa = number - number_disabled_2fa
    cprint(
        f"2FA enabled: {number_enabled_2fa} ({number_enabled_2fa / number:.0%})",
        "green",
    )
    cprint(
        f"2FA disabled: {number_disabled_2fa} ({number_disabled_2fa / number:.0%})",
        "red",
    )

    for user in disabled_2fa:
        print(f"{user.login}\t{user.name}")
    print()


print("MEMBERS")

members = list(org.get_members())
members_disabled_2fa = list(org.get_members("2fa_disabled"))

summarise(members, members_disabled_2fa)

print("COLLABORATORS")

collaborators = list(org.get_outside_collaborators())
collaborators_disabled_2fa = list(org.get_outside_collaborators("2fa_disabled"))

summarise(collaborators, collaborators_disabled_2fa)

print("COMBINED")

combined = members + collaborators
combined_disabled_2fa = members_disabled_2fa + collaborators_disabled_2fa

summarise(combined, combined_disabled_2fa)
