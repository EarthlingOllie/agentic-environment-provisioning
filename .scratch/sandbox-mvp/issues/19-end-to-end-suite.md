# 19: End-to-end suite on a sudo-capable Linux runner

**What to build:** A CI job that exercises the whole product as a user would, including the privileged parts unit and integration tests can't reach: `sudo sandbox setup`, `up` of the fixture repos, HTTPS from the host and from the agent, `down`, and `destroy` (story 111; spec: Testing Decisions, Layers).

**Blocked by:** 13 (extra hosts and Vite), 17 (destroy), 18 (setup)

**Status:** ready-for-agent

- [ ] Runs on a Linux runner with passwordless sudo; separate from the per-push unit/integration jobs
- [ ] Covers setup → `up` (two repos sharing `mysql`, a web app with an extra host and an init hook) → HTTPS via real `/etc/hosts` from host and agent → `down` → `destroy` → `setup --uninstall`
- [ ] Two sets provisioned in parallel both succeed with no port collisions
- [ ] A documented manual macOS checklist to run before each release
