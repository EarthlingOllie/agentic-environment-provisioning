"""YAML file helpers that turn parse and validation failures into field-level SandboxErrors."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from sandbox.errors import SandboxError


def read_yaml(path: Path) -> object:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SandboxError(f"cannot read {path}: {exc.strerror or exc}") from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SandboxError(f"{path}: invalid YAML: {exc}") from exc


def validate_file[M: BaseModel](model: type[M], data: object, source: Path) -> M:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise SandboxError(describe_validation_error(exc, source)) from exc


def describe_validation_error(error: ValidationError, source: Path) -> str:
    lines = [f"{source}: {error.error_count()} validation error(s)"]
    for detail in error.errors(include_url=False):
        location = ".".join(str(part) for part in detail["loc"]) or "(top level)"
        lines.append(f"  {location}: {detail['msg']}")
    return "\n".join(lines)


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
