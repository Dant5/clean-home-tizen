# TV/soundbar DNS protection companion

**Optional companion; manual commissioning required.** See [the deployment and recovery guide](../../docs/DNS-PROTECTION.md). This companion connects Clean Home to a dedicated [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) instance. It does not implement DNS, change a router, install on a TV or execute native TV commands.

- `prepare.py`: creates an owner-only resolver profile and separate limited TV connection. No existing profile is overwritten.
- `compose.yaml`: reviewed, digest-pinned resolver with explicit persistent mounts, loopback administration, restricted capabilities and no automatic startup.
- `compose.production.yaml`: deliberate startup policy for later commissioning.
- `bridge.py`: standard-library Python 3.12 adapter. Runs without root. Owner-local `--action` controls provide recovery without a TV update. Only combined/per-device status and protection enable/disable/bounded pauses for the dedicated instance are available. Controls apply to both configured devices.
- `cleanhome-privacy.service`: hardened service template, not an installed service.

The bridge accepts only the configured TV's source address, exact server Host, a separate random capability and an allowed Origin. It never trusts a caller-supplied client address or forwarded headers. Every control rechecks AdGuard's exact configured TV/soundbar allowlist and rejects unexpected per-client settings. Do not share this resolver with the household or reuse its administrator API for other devices. Source IP is a scope check, not cryptographic device identity; protect the LAN. The TV capability cannot change domains, upstreams, access lists, logs, packages, files or services.

Administration stays on IPv4 loopback with a separate password. The adapter authenticates with AdGuard’s native session cookie, held only in memory, so each scope/statistics read does not repeat an expensive password hash. An expired session is renewed for a read at most once; a protection setter is never automatically replayed. Redirects remain refused and every control still performs its fresh scope checks. HTTP from the TV is currently LAN-only plaintext, including its limited capability; upstream DNS encryption does not encrypt this connection. Do not expose either service through port forwarding, Tailscale Funnel or an unauthenticated proxy. Trusted HTTPS on older TVs needs separate certificate qualification; no TLS checks are disabled here.

The bridge keeps a short in-memory aggregate cache, with no second query database. An optional lifetime counter stores only counts, dates and private client identity; no domains. Counts use the configured local calendar day, exact TV/soundbar attribution and at most 20,000 records / seven calendar days per refresh. If bounded pagination stops early, it explicitly reports a partial log. Percentages describe recorded DNS queries, not tracking prevented. Domain categories are unavailable unless the upstream supplies them; block reasons and source lists remain available. Lists and sampled DNS transport are reported separately from full-path coverage, which is not established.

## Tests

```sh
.local/venv/bin/python -m pytest -q tests/test_dns_protection.py tests/test_dns_session.py
npm run check:dns
```

The actual AdGuard integration is opt-in: prepare a loopback-only test profile, start the pinned resolver, then run:

```sh
python3 scripts/check-dns-lab.py --profile .local/dns-protection/lab
python3 scripts/check-dns-restore.py
```

These use controlled test queries, not TV traffic. The restore rehearsal deliberately refuses to overwrite earlier evidence. Stop the disposable lab with its explicit project name and private environment file; do not use global Docker cleanup/pruning.

## Optional dashboard counters (source preparation only)

The dashboard cards show **Blocked today**, **Lookups today**, and **Lifetime blocked**. Lifetime starts when the persistent counter is enabled; it never estimates earlier activity. Without a configured counter it shows an em dash, not zero. Known gaps or a partial/reset query log make the total an explicit **at least** count (≥). Counts remain separately attributed to TV and soundbar.

For later approved deployment, install `lifetime.py` alongside `bridge.py`, create a private service-owned state directory under the existing protected resolver data root, add that exact directory to the service's `ReadWritePaths`, and set `lifetime_file` in its private configuration to a file there. Include the complete directory in existing consistent encrypted backup/restore coverage. Restoring an older state can lose counts; subsequent incomplete history must retain the lower-bound warning. No automatic counter reset or migration is provided. An optional five-minute worker in the existing adapter collects counts even while the TV page is closed. It reuses available logs, avoids unchanged writes and adds no service or system timer. If collection is unavailable for more than five days, history continuity is conservatively marked incomplete. This is a recorded counter, not proof that every TV request used the resolver.

`router_counters.py` is an **owner-run on-demand exporter** for the exact audited stock-ASUS rule shape. It calls the existing fixed `router-admin firewall` read, strips all addresses/raw rules and publishes only UDP/TCP DROP packet counts and a timestamp. Set `TV_IP` privately to the verified TV address before running:

```sh
python3 tools/dns-protection/router_counters.py --tv-ip "$TV_IP" --output /private-owner-managed-directory/router-counters.json
```

For later deployment, install `router_counters.py` alongside the adapter and set `router_counter_file` to a sanitised snapshot in a service-readable, owner-managed directory. **Do not give the adapter access to the administrator key, Docker socket, sudo or router-management profile.** No collector or monitoring job is installed here. If automated refresh is desired, review a fixed read/export hook in the existing host health workflow separately, including recovery and failure tests. A snapshot older than two minutes is unknown; stale counts never become a claim of active enforcement. `/v1/enforcement` uses the same exact TV source, Host, Origin and capability checks as status and has no setter or command parameters.

These packet counts cover all external plain DNS destinations on port 53, not just Google. They include retries and controlled probes and reset on firewall reload/reboot. They are **not daily/lifetime lookup counts**, are never added to the AdGuard chart/totals, and do not establish encrypted-DNS coverage. Soundbar view explicitly says the router rule applies only to the TV. Pause/disable changes AdGuard blocklists, not router rules; router Undo remains separate.
