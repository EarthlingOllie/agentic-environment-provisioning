# 04: Rollback, fail-fast, and the `up` state table

**What to build:** `up` behaves safely whatever state it finds. A failed `up` rolls back the set's own infrastructure (leaving worktrees), even on Ctrl-C. `up` decides what to do from the set directory: full provision, resume, no-op, or restart with `--recreate` (stories 32, 36, 92–95, 106–109; spec: Lifecycle state table, Concurrency).

**Blocked by:** 03 (Compose single repo)

**Status:** ready-for-agent

- [ ] All validation (plan, `.sandbox/`, and hooks for later checks such as dedup, hostname clashes and agent image) completes before any container starts
- [ ] Steps within a set run under structured asyncio (`TaskGroup`) and fail fast
- [ ] On failure, rollback removes the set's containers/network/volumes but keeps worktrees and plan, so rerunning `up` resumes
- [ ] Rollback is shielded from cancellation: Ctrl-C mid-`up` leaves no orphaned containers
- [ ] No set directory → full provision; directory and plan but nothing running → resume (skip worktree creation, run Compose); already running → no-op, exit 0, print bindings
- [ ] `--recreate` restarts a running set
- [ ] One set's failure never affects another set provisioned by a parallel process
