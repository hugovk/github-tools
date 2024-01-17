from __future__ import annotations

import pytest

from bpo_redirecter import do_lines


@pytest.mark.parametrize(
    "filename, old_line",
    [
        (
            "whatsnew/3.2.rst",
            ".. XXX https://bugs.python.org/issue?%40search_text=datetime&%40sort=-activity",
        ),
        (
            "whatsnew/2.7.rst",
            "feature or the issue on https://bugs.python.org in which a change was",
        ),
        (
            "whatsnew/2.6.rst",
            "set up at https://bugs.python.org.  One installation of Roundup can",
        ),
        (
            "whatsnew/2.6.rst",
            "  https://bugs.python.org",
        ),
        (
            "tools/extensions/pyspecific.py",
            "ISSUE_URI = 'https://bugs.python.org/issue?@action=redirect&bpo=%s'",
        ),
        (
            "tools/extensions/pyspecific.py",
            "# Support for marking up and linking to bugs.python.org issues",
        ),
        (
            "library/ssl.rst",
            "                       ('DNS', 'bugs.python.org')",
        ),
        (
            "library/http.client.rst",
            '   >>> conn = http.client.HTTPConnection("bugs.python.org")',
        ),
    ],
)
def test_do_lines_bpo_no_change(filename, old_line) -> None:
    assert do_lines([old_line], filename) == [old_line]


@pytest.mark.parametrize(
    "filename, old_line, expected",
    [
        (
            "tutorial/inputoutput.rst",
            "   See also https://bugs.python.org/issue17852",
            "   See also https://github.com/python/cpython/issues/62052",
        ),
        (
            "library/curses.rst",
            "      * A `bug in ncurses "
            "<https://bugs.python.org/issue35924>`_, the backend",
            "      * A `bug in ncurses "
            "<https://github.com/python/cpython/issues/80105>`_, the backend",
        ),
        (
            "c-api/typeobj.rst",
            "      `bug 40217 <https://bugs.python.org/issue40217>`_, doing this",
            "      `bug 40217 <https://github.com/python/cpython/issues/84398>`_, "
            "doing this",
        ),
        (
            "howto/logging-cookbook.rst",
            "https://bugs.python.org/issue3770).",
            "https://github.com/python/cpython/issues/48020).",
        ),
        (
            "two-in-a-row.rst",
            "to https://bugs.python.org/issue3771 and https://bugs.python.org/issue3772.",
            "to https://github.com/python/cpython/issues/48021 and "
            "https://github.com/python/cpython/issues/48022.",
        ),
    ],
)
def test_do_lines_bpo_with_change(filename, old_line, expected) -> None:
    assert do_lines([old_line], filename) == [expected]


@pytest.mark.parametrize(
    "filename, old_line, expected",
    [
        (
            "Doc/library/logging.rst",
            "      :issue:`28524` for more information about this change.",
            "      :gh:`72710` for more information about this change.",
        ),
        (
            "Doc/whatsnew/3.3.rst",
            "      (Contributed by Ezio Melotti in :issue:`15114`, and :issue:`14538`,",
            "      (Contributed by Ezio Melotti in :gh:`59319`, and :gh:`58743`,",
        ),
    ],
)
def test_do_lines_issue_with_change(filename, old_line, expected) -> None:
    assert do_lines([old_line], filename) == [expected]
