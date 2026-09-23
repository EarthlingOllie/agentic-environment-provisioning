"""CLI shape: `sandbox [SET] <verb>`, reserved verbs, and the platform gate."""

import sys

import pytest

from tests.conftest import Env, invoke
from tests.fakes import FakeGit


def test_help_shows_set_verb_shape(env: Env) -> None:
    result = invoke(["--help"], FakeGit())
    assert result.exit_code == 0
    assert "[SET] VERB" in result.output


@pytest.mark.parametrize("verb", ["up", "status", "destroy", "templates"])
def test_set_name_colliding_with_a_verb_is_rejected(env: Env, verb: str) -> None:
    env.make_repo_dir("api")
    result = invoke([verb, "up", "--repos", "api"], FakeGit())
    assert result.exit_code == 2
    assert f"{verb!r} is a sandbox verb and cannot be used as a set name" in result.stderr
    assert not env.sets_root.exists()


@pytest.mark.parametrize("name", ["Jira-123", "a.b", "jira_123", "a" * 64, "x-"])
def test_invalid_set_name_is_rejected(env: Env, name: str) -> None:
    result = invoke([name, "up", "--repos", "api"], FakeGit())
    assert result.exit_code == 2
    assert "invalid set name" in result.stderr


def test_verb_without_a_set_explains_the_shape(env: Env) -> None:
    result = invoke(["up", "--repos", "api"], FakeGit())
    assert result.exit_code == 2
    assert "up needs a set: sandbox SET up" in result.stderr


def test_set_without_a_verb_is_an_error(env: Env) -> None:
    result = invoke(["jira-123"], FakeGit())
    assert result.exit_code == 2
    assert "missing verb" in result.stderr


def test_repo_names_without_repos_flag_are_rejected(env: Env) -> None:
    result = invoke(["jira-123", "up", "api"], FakeGit())
    assert result.exit_code == 2
    assert "did you mean --repos api" in result.stderr


@pytest.mark.parametrize("platform", ["win32", "cygwin"])
def test_windows_is_unsupported(env: Env, monkeypatch: pytest.MonkeyPatch, platform: str) -> None:
    monkeypatch.setattr(sys, "platform", platform)
    result = invoke(["jira-123", "up", "--repos", "api"], FakeGit())
    assert result.exit_code != 0
    assert "unsupported platform" in result.stderr
    assert not env.sets_root.exists()
