"""The plan schema shared by set plans and templates."""

import pytest
from pydantic import ValidationError

from sandbox.plan import SetPlan, TemplatePlan
from tests.conftest import Env, invoke
from tests.fakes import FakeGit


def test_set_plan_requires_base_but_template_does_not() -> None:
    data = {"repos": {"api": {"source": "/code/api"}}}
    template = TemplatePlan.model_validate(data)
    assert template.repos["api"].base is None
    with pytest.raises(ValidationError) as caught:
        SetPlan.model_validate(data)
    assert [e["loc"] for e in caught.value.errors()] == [("repos", "api", "base")]


def test_source_must_be_absolute() -> None:
    with pytest.raises(ValidationError) as caught:
        TemplatePlan.model_validate({"repos": {"api": {"source": "code/api"}}})
    [error] = caught.value.errors()
    assert error["loc"] == ("repos", "api", "source")
    assert "absolute" in error["msg"]


@pytest.mark.parametrize("model", [SetPlan, TemplatePlan])
def test_set_name_never_appears_in_a_plan(model: type[SetPlan] | type[TemplatePlan]) -> None:
    with pytest.raises(ValidationError) as caught:
        model.model_validate(
            {"name": "jira-123", "repos": {"api": {"source": "/a", "base": "main"}}}
        )
    assert [e["loc"] for e in caught.value.errors()] == [("name",)]


def test_repos_must_not_be_empty_and_names_are_checked() -> None:
    with pytest.raises(ValidationError) as caught:
        SetPlan.model_validate({"repos": {}})
    assert caught.value.errors()[0]["loc"] == ("repos",)
    with pytest.raises(ValidationError) as caught:
        SetPlan.model_validate({"repos": {"sandbox.yaml": {"source": "/a", "base": "main"}}})
    assert "invalid repo name" in str(caught.value)


def test_plan_round_trips_through_yaml() -> None:
    plan = SetPlan.model_validate(
        {"repos": {"api": {"source": "/code/api", "base": "release/2.4"}}}
    )
    assert plan.to_yaml() == "repos:\n  api:\n    source: /code/api\n    base: release/2.4\n"


def test_invalid_plan_on_disk_fails_with_field_level_errors(env: Env) -> None:
    set_dir = env.set_dir("jira-123")
    set_dir.mkdir(parents=True)
    (set_dir / "sandbox.yaml").write_text("name: jira-123\nrepos:\n  api:\n    source: code/api\n")
    result = invoke(["jira-123", "up"], FakeGit())
    assert result.exit_code == 1
    plan_file = set_dir / "sandbox.yaml"
    assert f"{plan_file}: 3 validation error(s)" in result.stderr
    assert "repos.api.source: Value error, must be an absolute path" in result.stderr
    assert "repos.api.base: Field required" in result.stderr
    assert "name: Extra inputs are not permitted" in result.stderr
