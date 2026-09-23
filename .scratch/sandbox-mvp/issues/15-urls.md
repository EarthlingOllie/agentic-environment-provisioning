# 15: `sandbox SET urls`, with `--json`

**What to build:** A developer can list every host-resolvable address in a set: web apps as `https://` URLs (including extra hosts and Vite) and backing services as `host:port`, each with its IP (stories 90, 91).

**Blocked by:** 12 (HTTPS web apps), 14 (status)

**Status:** ready-for-agent

- [ ] Web apps listed as `https://<host>.<set>.test` with IP; backing services as `<service>.<set>.test:<port>` with IP
- [ ] `--json` prints the same Pydantic model as the table
- [ ] Works on a stopped set from its sticky leases, marking it as not running
