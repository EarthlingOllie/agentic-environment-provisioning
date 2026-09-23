"""The ``sandbox`` command line: ``sandbox [SET] <verb> [OPTIONS]``.

The optional leading SET is peeled off before Click dispatches the verb and stored in the
context's shared ``meta``, so every verb can read it with :func:`current_set`. Dependencies
(git today; Compose and mkcert later) travel in ``ctx.obj`` so tests can invoke the app
in-process with fakes: ``CliRunner().invoke(app, [...], obj=Deps(git=FakeGit()))``.
"""

import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Final, NoReturn

import typer
from typer.core import TyperGroup

from sandbox.config import load_config
from sandbox.errors import SandboxError
from sandbox.git import Git, SubprocessGit
from sandbox.names import RESERVED_VERBS, validate_set_name
from sandbox.platforms import ensure_supported_platform
from sandbox.provisioner import Provisioner
from sandbox.worktrees import WorktreeOutcome

SET_META_KEY: Final = "sandbox.set"


@dataclass
class Deps:
    """External collaborators, swappable for fakes in tests."""

    git: Git = field(default_factory=SubprocessGit)


class SetFirstGroup(TyperGroup):
    """A group that accepts an optional set name before the verb."""

    def parse_args(self, ctx: Any, args: list[str]) -> list[str]:  # noqa: ANN401 - Click's Context is private in Typer
        if args and not args[0].startswith("-"):
            first = args[0]
            if first in RESERVED_VERBS:
                if len(args) > 1 and args[1] in RESERVED_VERBS:
                    _fail(f"{first!r} is a sandbox verb and cannot be used as a set name")
            else:
                try:
                    ctx.meta[SET_META_KEY] = validate_set_name(first)
                except SandboxError as exc:
                    _fail(str(exc))
                args = args[1:]
                if not args:
                    _fail(f"missing verb: sandbox {first} <verb>")
        return super().parse_args(ctx, args)


def _fail(message: str) -> NoReturn:
    typer.echo(f"error: {message}", err=True)
    raise typer.Exit(code=2)


app = typer.Typer(
    cls=SetFirstGroup,
    name="sandbox",
    help="Provision isolated multi-repo sets (worktrees, services, agent) for coding agents.",
    subcommand_metavar="[SET] VERB [ARGS]...",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_enable=False,
)


@app.callback()
def _root(ctx: typer.Context) -> None:
    try:
        ensure_supported_platform()
    except SandboxError as exc:
        _fail(str(exc))
    if ctx.obj is None:
        ctx.obj = Deps()


def current_set(ctx: typer.Context, verb: str) -> str:
    name = ctx.meta.get(SET_META_KEY)
    if not isinstance(name, str):
        _fail(f"{verb} needs a set: sandbox SET {verb}")
    return name


def _deps(ctx: typer.Context) -> Deps:
    deps = ctx.obj
    if not isinstance(deps, Deps):
        raise TypeError("sandbox CLI context object must be a Deps instance")
    return deps


def _warn(message: str) -> None:
    typer.echo(f"warning: {message}", err=True)


@app.command()
def up(
    ctx: typer.Context,
    use_repos: Annotated[
        bool,
        typer.Option(
            "--repos",
            help="Build a new set from the NAME directories in the current directory.",
        ),
    ] = False,
    names: Annotated[
        list[str] | None,
        typer.Argument(metavar="NAME...", show_default=False),
    ] = None,
) -> None:
    """Create the set (or resume it) with a worktree per repo on agent/SET."""
    set_name = current_set(ctx, "up")
    if use_repos and not names:
        _fail("--repos needs at least one repo name: sandbox SET up --repos NAME...")
    if names and not use_repos:
        _fail(f"unexpected argument(s) {' '.join(names)}: did you mean --repos {' '.join(names)}?")
    repos = names if use_repos else None
    try:
        config = load_config()
        provisioner = Provisioner(config, _deps(ctx).git, _warn)
        result = asyncio.run(provisioner.up(set_name, repos=repos, cwd=Path.cwd()))
    except SandboxError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"set {result.set_name}: {result.set_dir}")
    typer.echo(f"  plan: {result.plan_file}{' (created)' if result.plan_created else ''}")
    for worktree in result.worktrees:
        detail = {
            WorktreeOutcome.CREATED: f"created from {worktree.base}",
            WorktreeOutcome.REUSED_BRANCH: "existing branch reused",
            WorktreeOutcome.EXISTING: "already present",
        }[worktree.outcome]
        typer.echo(f"  {worktree.repo}: {worktree.path} [{worktree.branch}, {detail}]")


def main() -> None:
    """Console-script entry point."""
    try:
        ensure_supported_platform()
    except SandboxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    app()
