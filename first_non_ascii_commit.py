"""
Find first and total commits with non-ASCII messages and authors
"""
import time

from git import Repo  # pip install GitPython


def print_info(commit: str) -> None:
    # print(commit)
    print(commit.author)
    print(commit.message)
    print(time.asctime(time.gmtime(commit.committed_date)))
    print(f"https://github.com/python/cpython/commit/{commit}")


def main() -> None:
    repo = Repo("~/github/cpython")
    non_ascii_commit_messages = non_ascii_authors = 0
    for commit in repo.iter_commits("main", reverse=True):
        if not commit.message.isascii():
            if not non_ascii_commit_messages:
                print("First non-ASCII commit message:\n")
                print_info(commit)
            non_ascii_commit_messages += 1

    print()

    for commit in repo.iter_commits("main", reverse=True):
        if not commit.author.name.isascii():
            if not non_ascii_authors:
                print("First non-ASCII commit author:\n")
                print_info(commit)
            non_ascii_authors += 1

    print()
    print("Total non-ASCII commit messages:", non_ascii_commit_messages)
    print("Total non-ASCII commit authors:", non_ascii_authors)


if __name__ == "__main__":
    main()
