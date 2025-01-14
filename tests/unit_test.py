from unittest import mock
from typing import Any, Sequence, Tuple

from py.path import local as LocalPath


class FakeCircleci:
    def __init__(self, args: Sequence[str], **kwargs: Any) -> None:
        self.args = args

    def communicate(self, stdin: bytes) -> Tuple[bytes, bytes]:
        lines = []
        for line in stdin.decode("utf-8").split():
            if "IncludedTestCase" in line:
                lines.append(line)
        return "\n".join(lines).encode("utf-8"), b""


def test_help_message(testdir: LocalPath) -> None:
    result = testdir.runpytest("--help")
    result.stdout.fnmatch_lines(
        [
            "circleci-parallelized:",
            "*--circleci-parallelize",
            "*Enable parallelization across CircleCI containers.",
        ]
    )


@mock.patch("subprocess.Popen", FakeCircleci)
def test_with_circleci_parallelize(testdir: LocalPath) -> None:
    testdir.makepyfile(
        """
import unittest

class IncludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True

class ExcludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True
        """
    )
    result = testdir.runpytest("--circleci-parallelize")
    result.stdout.fnmatch_lines(
        ["*collected 2 items", "running 1 items due to CircleCI parallelism"]
    )
    assert result.ret == 0


@mock.patch("subprocess.Popen", FakeCircleci)
def test_with_circleci_parallelize_and_quiet(testdir: LocalPath) -> None:
    testdir.makepyfile(
        """
import unittest

class IncludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True

class ExcludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True
        """
    )
    result = testdir.runpytest("--circleci-parallelize", "-q")
    result.stdout.fnmatch_lines(["1 passed*"])
    assert not any("CircleCI parallelism" in line for line in result.stdout.lines)
    assert result.ret == 0


@mock.patch("subprocess.Popen", FakeCircleci)
def test_with_circleci_parallelize_and_verbose(testdir: LocalPath) -> None:
    testdir.makepyfile(
        """
import unittest

class IncludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True

class ExcludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True
        """
    )
    result = testdir.runpytest("--circleci-parallelize", "-v")
    result.stdout.fnmatch_lines(
        [
            "*collected 2 items",
            (
                "running 1 items due to CircleCI parallelism: "
                "test_with_circleci_parallelize_and_verbose.IncludedTestCase"
            ),
        ]
    )
    assert result.ret == 0


@mock.patch("subprocess.Popen", FakeCircleci)
def test_with_circleci_parallelize_and_no_included_tests(testdir: LocalPath) -> None:
    testdir.makepyfile(
        """
import unittest

class ExcludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True
        """
    )
    result = testdir.runpytest("--circleci-parallelize")
    result.stdout.fnmatch_lines(
        ["*collected 1 item", "running 0 items due to CircleCI parallelism"]
    )
    assert result.ret == 0


@mock.patch("subprocess.Popen", FakeCircleci)
def test_without_circleci_parallelize(testdir: LocalPath) -> None:
    testdir.makepyfile(
        """
import unittest

class IncludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True

class ExcludedTestCase(unittest.TestCase):
    def test_something(self):
        assert True
        """
    )
    result = testdir.runpytest("-v")
    result.stdout.fnmatch_lines(
        [
            "*collected 2 items",
            "*IncludedTestCase::test_something PASSED*",
            "*ExcludedTestCase::test_something PASSED*",
        ]
    )
    assert result.ret == 0
