# Q60B privacy controls: implementation proposal

**Status: research and design. No privacy/debloat controls have been deployed.** Keep Clean Home as the launcher, with its existing appearance, saved apps, Samsung Home escape and native Home/startup assignment. This proposal is specific to QA55Q60BAWXXY / T-NKLBUABC-1720.7 / Tizen 6.5; broader widget compatibility is separate.

Before any update, identify the installed app and resource hashes. Repository version labels, a stable tag and the latest release can describe three different builds. Preserve the actual installed signed widget, matching author identity, current preferences and device-bound native originals. A launcher/certificate backup does not contain other apps' private accounts or pairings. [Update/recovery boundary](BING-DAILY.md#later-installation-and-rollback-not-performed).

## Evidence and boundaries

The reference Q60B supports non-root SDK UID-901 reads of named Home/privacy preferences, AUL lifecycle data and package/app-disable metadata through read-only SQLite. The protected consent database was not readable in that context. Reading a preference does not prove that changing it is safe, that its enum matches another firmware, or that a consent has been withdrawn.

The installed widget and the public desktop helper also have different privileges. The ordinary web widget cannot execute vconf/SQL because a PC-side SDK helper can. The audited secure developer connection worked through the existing authenticated TizenSdb.Core/Apps2Samsung path; the lightweight Python client's handshake did not. Qualify that transport before promising live native controls through the generic companion. Reuse a maintained transport rather than implement another authentication protocol.

The private legacy repository's Vetro/root/reaper records describe UA43DU7660KLXL, Tizen 9 and a different package identity. They are not Q60B qualification. Its documents also record a rejected Home remap and a microphone regression during a tracking-service batch. Do not copy those defaults, originals or boot chain onto the Q60B.

Owner inventories, consent states, network addresses, signed packages, profiles and raw diagnostics stay outside Git. Public reporting remains opt-in and does not acquire an app inventory, advertising identifier or raw native log.

## Controls in the existing interface

Add **Settings → Samsung → Privacy & optional features**, using the current rows, typography, focus and Back behavior. No new launcher, dashboard or always-running watcher.

| Row | Initial behavior | Evidence shown |
|---|---|---|
| Samsung privacy choices | Open a discovered Samsung privacy application, with Settings fallback | Availability; successful launch is not proof a consent changed |
| Viewing information / ACR | Explain the Samsung consent setting; guide the user there | Verified consent only if actually readable; otherwise “Check in Samsung settings” |
| Personalised ads | Read LAT only through `isLATEnabled()` after the appropriate privilege is declared and tested | Supported boolean or unavailable; never request TIFA/PSID |
| HbbTV and Do Not Track | Explain effect and open the relevant settings route where supported | Typed native snapshot only after menu/enum correlation; stale snapshots labelled |
| Optional TV features | List reviewed feature choices and what would stop working | No substring-based bulk disable or default action |
| Network privacy | Explain/export reviewed exact-host candidates after traffic evidence | Candidate / observed / trial / verified, never a false “blocked” badge |
| Recovery | Show scope and Undo availability for each implemented native action | Device-bound originals, verification result and partial/unknown state |

“Service running”, “package enabled”, “recognition state”, “consent”, “LAT” and “network upload” are different observations. ACR/advertising processes can exist while consent-dependent behavior is off. Unknown/unreadable does not mean off or on. Do Not Track is a request, not a guarantee that collection stops. LAT limits personalised advertising; it does not remove all ads. Clearing an advertising identifier is not an opt-out.

Samsung documents optional Viewing Information Services and advertising choices through Privacy Choices/Settings. Australian HbbTV supplies Freeview interactive/on-demand integration; disabling it has a functional cost. Keep account/mandatory Smart Hub agreements, voice/microphone, apps, DRM, picture/sound, HDMI/eARC/CEC, casting and updates outside default cleanup.

## Implementation boundaries

1. **Widget adapter:** extend the existing `FrameDevice` boundary with availability/error handling, a discovered privacy-app shortcut and optional LAT boolean. Call no advertising-ID API. Keep remote navigation and normal app launching independent of a pending check.
2. **State model:** each observation carries source, time, type, value/unknown and reason. Preserve raw enum values separately from interpretation. A user-confirmed menu observation is explicitly different from a live getter. Pause work when the screen closes; ignore late callbacks and avoid background polling.
3. **Optional native setup:** reuse the separate Home Setup/helper infrastructure for on-demand computer-assisted operations. Keep fixed action/key allowlists, exact reference firmware/architecture/UID guards and a real rollback record. A TV-local native execution route requires separate feasibility and entitlement proof; do not silently add a root service or make the PC a permanent dependency.
4. **Native transactions:** introduce a privacy-specific record separate from immutable Home/Last App/update originals. Read the current value, validate exact type/enum and baseline, persist the original locally, change one reviewed setting, independently read back, and record confirmed/unknown results. No automatic retries after an ambiguous write. Undo checks device identity and drift; a failed restoration remains visibly failed.
5. **Package controls:** use a supported package-management operation only after dependency and rollback validation. Do not write package-manager or consent databases directly. A false `package_system` flag is not permission or evidence that a vendor component is disposable. Protect Samsung Home, settings/privacy UI, account/network/time/certificate/update functions, app runtimes and DRM. Conservatively protect Vetro's known Smart Hub/adagent dependency until this model is understood.
6. **DNS/export:** keep blocking outside the ordinary widget. Exact-host candidates carry provenance and review state. Parent/suffix overlap with protected services must be rejected; no whole Samsung domain trees. Preserve firmware/manual updates, sign-in, certificates, clock/online checks, store, licences, streams/CDNs and LAN streaming. Do not import Vetro's policy of allowing update-server blocking.

## Reuse from Vetro

The reviewed [MIT source snapshot](https://github.com/andrearicci93/vetro/tree/1463f8af0890a2bc756fd197c56e265ee04d7759) separates privacy parsing, package-target validation and domain provenance. Those patterns are useful; importing actual source later requires its notices and focused tests. Preserve truthful unavailable states and dependency protections.

Do not import root payloads, boot hooks, service reacquisition, reaper/keeper loops, generic `/exec`, broad SQL disable batches, another TV's IDs/recovery data, or a domain list as a tested Q60B profile. Its domain document distinguishes Q80A firmware strings from public reports and guesses; none alone proves Q60B traffic or safe blocking. No Vetro code or payload has been incorporated by this proposal.

## Stages and acceptance gates

| Stage | Work | Evidence needed before advancing |
|---|---|---|
| 0 — Audit | Identify actual installed build, firmware, Home routing, known optional components and artifacts | Private live reads/hashes; separate historical and other-TV records; no update to identify version |
| 1 — Read-only UI | Add privacy shortcut, optional LAT read, state model and help in existing Settings | Mocked current/85 tests for missing privilege, unknown/stale values, denied launch, focus, Back/cancel, late completion; packaged checks across supported engines; physical shortcut/remote rehearsal |
| 2 — Normal settings | Observe exact Samsung consent/HbbTV/DNT menus; make only selected ordinary changes | Record before/after states and functional tradeoffs; preserve mandatory account agreements; verify voice, apps, Home and relevant broadcaster features |
| 3 — Narrow native actions | Resolve authenticated transport; qualify one needed control at a time | Exact key/type/enum and documented meaning; original backup copied/verified through existing recovery; rollback/readback/drift/partial-failure tests; no root or persistent service; explicit pause for any poorly understood change |
| 4 — Network trial | Establish suitable per-TV observations; propose a minimal exact-host rule | Check all configured resolvers/fallbacks and app-controlled DNS; no global DNS switch or new resolver service without deployment review; restore configuration immediately on failures; verify account/DRM/apps/manual-update reachability without performing an update |
| 5 — Root decision | Consider only a specific remaining useful capability with no acceptable earlier route | Separate proposal with exact Q60B evidence, effects, recovery and risk; owner approval before rooting, protected/persistent system changes, package removal or update-behavior changes |

A native stop or disable is not automatically safe because it is reversible in theory: the service may restart, dependencies may fail or access needed for recovery may disappear. Root is not a default stage to execute after the table. No unattended enforcement or performance promise is part of this proposal.

## Recovery and testing requirements

Before a later installation, retain the exact same-author previous widget and current own-app preferences, and verify the affected encrypted recovery copy. Update only Clean Home in place; preserve saved favourites/manual IDs. Do not reinstall other apps or rerun native Home setup to add a settings page.

Meaningful workflow tests cover profile mismatch, unavailable privilege/getter, raw value with unknown meaning, timeout after a possible write, failed readback, interrupted save, wrong-device Undo, drift, incomplete rollback, cancel and app relaunch. UI tests must not equate a mock getter with real hardware. DNS tests cover case/trailing-dot normalization, invalid/suffix-overlapping hosts, protected update/account/licence routes and exact export semantics for the selected resolver.

Physical qualification later includes Home/Samsung Home escape, ordinary standby/wake, saved apps/accounts, Nuvio/Moonlight, microphone, HDMI/audio/eARC and the features affected by each choice. No deliberate firmware installation is needed for a privacy test. Keep change batches small and retain the previous baseline.

## Sources

- [Samsung Q60B Australian support/manual entry](https://www.samsung.com/au/support/model/QA55Q60BAWXXY/)
- [Samsung ACR and optional viewing information](https://www.samsung.com/us/support/answer/ANS10010616/)
- [Samsung Australia advertising privacy choices](https://www.samsung.com/au/info/ads-privacy/)
- [Samsung Australia HbbTV and disabling it](https://www.samsung.com/au/support/tv-audio-video/accessing-freeview-hbbtv-on-demand-tv/)
- [Public AdInfo interface: LAT read, no setter](https://developer.samsung.com/smarttv/develop/api-references/samsung-product-api-references/adinfo-api.html)
- [Samsung TIFA/LAT guide](https://developer.samsung.com/smarttv/develop/guides/unique-identifiers-for-smarttv/tizen-id-for-advertising.html)
- [Pinned Vetro privacy parser](https://github.com/andrearicci93/vetro/blob/1463f8af0890a2bc756fd197c56e265ee04d7759/app/service/privacy.js), [target/dependency checks](https://github.com/andrearicci93/vetro/blob/1463f8af0890a2bc756fd197c56e265ee04d7759/app/service/debloat.js), [domain evidence and limits](https://github.com/andrearicci93/vetro/blob/1463f8af0890a2bc756fd197c56e265ee04d7759/app/docs/DOMAIN-FILTER.md)
