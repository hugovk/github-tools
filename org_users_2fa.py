"""
List users in an org with 2FA disabled

First create a GitHub token with repo scope and save to keyring:
$v python -m pip install -U keyring
$ keyring set github-tools github-token
Password for 'github-token' in 'github-tools':
"""
import argparse
import sys

import keyring
from github import Github  # pip install PyGithub
from termcolor import cprint  # pip install termcolor

# GITHUB_TOKEN = os.environ["GITHUB_TOOLS_REPO_TOKEN"]
GITHUB_TOKEN = keyring.get_password("github-tools", "github-token")


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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("org", help="GitHub organisation to check")
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        sys.exit("Error: GitHub token missing")
    g = Github(GITHUB_TOKEN, per_page=100)
    org = g.get_organization(args.org)
    all_results = []

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


if __name__ == "__main__":
    sys.exit(main())
