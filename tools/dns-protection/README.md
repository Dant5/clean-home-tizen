# TV/soundbar DNS protection companion

**Optional companion; manual commissioning required.** See [the deployment and recovery guide](../../docs/DNS-PROTECTION.md). This companion connects Clean Home to a dedicated [AdGuard Home](https://github.com/AdguardTeam/AdGuardHome) instance. It does not implement DNS, change a router, install on a TV or execute native TV commands.

- `prepare.py`: creates an owner-only resolver profile and separate limited TV connection. No existing profile is overwritten.
- `compose.yaml`: reviewed, digest-pinned resolver with explicit persistent mounts, loopback administration, restricted capabilities and no automatic startup.
- `compose.production.yaml`: deliberate startup policy for later commissioning.
- `bridge.py`: standard-library Python 3.12 adapter. Runs without root. Owner-local `--action` controls provide recovery without a TV update. Only combined/per-device status and protection enable/disable/bounded pauses for the dedicated instance are available. Controls apply to both configured devices.
- `cleanhome-privacy.service`: hardened service template, not an installed service.

The bridge accepts only the configured TV's source address, exact server Host, a separate random capability and an allowed Origin. It never trusts a caller-supplied client address or forwarded headers. Every control rechecks AdGuard's exact configured TV/soundbar allowlist and rejects unexpected per-client settings. Do not share this resolver with the household or reuse its administrator API for other devices. Source IP is a scope check, not cryptographic device identity; protect the LAN. The TV capability cannot change domains, upstreams, access lists, logs, packages, files or services.

Administration stays on IPv4 loopback with a separate password. The adapter authenticates with AdGuard’s native session cookie, held only in memory, so each scope/statistics read does not repeat an expensive password hash. An expired session is renewed for a read at most once; a protection setter is never automatically replayed. Redirects remain refused and every control still performs its fresh scope checks. HTTP from the TV is currently LAN-only plaintext, including its limited capability; upstream DNS encryption does not encrypt this connection. Do not expose either service through port forwarding, Tailscale Funnel or an unauthenticated proxy. Trusted HTTPS on older TVs needs separate certificate qualification; no TLS checks are disabled here.

The bridge keeps a short in-memory aggregate cache, with no second query database. Counts use the configured local calendar day, exact TV/soundbar attribution and at most 20,000 records / seven calendar days per refresh. If bounded pagination stops early, it explicitly reports a partial log. Percentages describe recorded DNS queries, not tracking prevented. Domain categories are unavailable unless the upstream supplies them; block reasons and source lists remain available. Lists and sampled DNS transport are reported separately from full-path coverage, which is not established.

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
