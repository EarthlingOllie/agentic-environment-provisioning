"""WorktreeManager: one git worktree per repo inside the set directory, on ``agent/<set>``."""

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from sandbox.git import Git
from sandbox.locking import file_lock


class WorktreeOutcome(StrEnum):
    CREATED = "created"
    REUSED_BRANCH = "reused-branch"
    EXISTING = "existing"


@dataclass(frozen=True)
class WorktreeResult:
    repo: str
    path: Path
    branch: str
    base: str
    outcome: WorktreeOutcome


class WorktreeManager:
    def __init__(self, git: Git, lock_dir: Path) -> None:
        self._git = git
        self._lock_dir = lock_dir

    def lock_path(self, source: Path) -> Path:
        """One lock per source repo, shared by every sandbox process on this machine."""
        digest = hashlib.sha256(str(source.resolve()).encode()).hexdigest()[:16]
        return self._lock_dir / f"worktree-{digest}.lock"

    async def ensure(
        self, *, repo: str, source: Path, path: Path, branch: str, base: str
    ) -> WorktreeResult:
        """Create the worktree unless it already exists.

        A surviving ``branch`` is checked out as-is (``base`` is ignored) so earlier agent work
        is picked up rather than lost. ``git worktree add`` mutates the source repo's ``.git``,
        so it runs under a per-source-repo lock.
        """
        if (path / ".git").exists():
            return WorktreeResult(repo, path, branch, base, WorktreeOutcome.EXISTING)
        async with file_lock(self.lock_path(source)):
            await self._git.prune_worktrees(source)
            if await self._git.branch_exists(source, branch):
                await self._git.add_worktree(source, path, branch, base=None)
                outcome = WorktreeOutcome.REUSED_BRANCH
            else:
                await self._git.add_worktree(source, path, branch, base=base)
                outcome = WorktreeOutcome.CREATED
        return WorktreeResult(repo, path, branch, base, outcome)
