# Native Samsung Home replacement: cross-repository source study

**Read-only research snapshot, 31 October 2026.** This branch contains upstream source for comparison, **not a cross-model installer, a tested patch or a proposal to ship their native binaries.** The referenced projects are independently maintained; all native Home APIs are undocumented and can change across Samsung firmware.

## The result in one paragraph

At least three physically different 2022/2024 Samsung TV models are documented using the same non-root native Home assignment family: **Q70B (Tizen 6.5), The Frame LS03D (Tizen 9), and S90D (Tizen 9)**. A contributor also reports success on a different Q60B (Tizen 6.5) via CleanFrame PR #5. They all use the TV's current main-app routing and Home preference, but their initial Smart Hub autostart states, derived startup keys, runtimes and cold-boot behaviour differ. Their reported hardware results are **not automatically compatibility results for Dant5's Clean Home tool**.

## Exact source snapshots (pinned; see licences)

| Original project | Source snapshot | Evidence | Licence |
| --- | --- | --- | --- |
| [Arn0 TV / NelsonEU](https://github.com/NelsonEU/arn0-tv/tree/b35c292e5bc63648cb8fef576bf5eacd9ea488d1) | `upstream/NelsonEU__arn0-tv/native/Control.cs`, `Query.cs`, `docs/setup-tv.md` | Q70B/QE65Q70BATXXC, Tizen 6.5, T-PTMDEUC-1720.7. Physical Home tested; cold boot not separately proved in this project. | MIT; copied `LICENSE` |
| [CleanFrame / nthnclrk](https://github.com/nthnclrk/CleanFrame/tree/58ac92a7b8f80047ca26e5b7097f5e1616762db0) | `upstream/nthnclrk__CleanFrame/scripts/native-home/Control.cs`, `run.py`, `README.md`, `app/device.js`, `docs/compatibility.md` | 2024 The Frame LS03D, Tizen 9, firmware 2130.0. Home from Netflix, native restore/reapply. Power-on/Art Mode has additional gaps. | MIT; copied `LICENSE` |
| [Couchroot / splitcipher](https://github.com/splitcipher/couchroot/tree/fd8a945588786c4af0c859064dbf52266be7091a) | `upstream/splitcipher__couchroot/tools/dotnet/Program.cs`, `docs/lab/devices/s90d/README.md` | 2024 S90D, Tizen 9, firmware 2130.0. Records main routing, boot, standby, native restoration, plus exploratory root-assisted diagnostics. | 0BSD; copied `LICENSE` |
| [CleanFrame contributor PR #5](https://github.com/nthnclrk/CleanFrame/pull/5) | **Source linked, NOT copied**. Unmerged contributor diff. | Different Q60B (QN43Q60BAFXZA, Tizen 6.5): author reports apply, restore, reapply, Home from Netflix and cold boot. | Part of project contribution; not merged or maintainer-confirmed |
| [CleanFrame contributor PR #2](https://github.com/nthnclrk/CleanFrame/pull/2) | **Source linked, NOT copied**. Unmerged contributor diff. | Same Q60B author reports native Samsung Home/Settings via targeted ApplicationControl and hidden cold-boot rendering fixes. | Part of project contribution; not merged or maintainer-confirmed |

The [chaosmanage/samsung-tv-launcher](https://github.com/chaosmanage/samsung-tv-launcher) repository returned **404 from the live GitHub API on 31 October 2026**, despite an indexed README claiming a working DU7660 Tizen 9 rootless Home implementation and discussing cold-boot black screens. Its source cannot be verified or copied from that live repository currently. Do not treat cached information as source-level confirmation or silently replace it with a mirror.

**Scope:** only selected native-control, runner, recovery, small Samsung-launch adapter and evidence files are copied. No assets, compiled executables, signatures, device-specific baselines, secrets, third-party SDK files or proprietary firmware. Keep attribution and licences with every redistribution; do not inadvertently package research files into the public WGT/setup ZIP.

## Shared native route: the proven common pattern

1. Query the current handler of the `http://tizen.org/appcontrol/operation/main` app-control operation using `bundle_create` + `aul_svc_set_operation` + `aul_get_default_app`.
2. Query baseline typed preferences with `vconf_get_str` / `vconf_get_int`; most stock Home owners in these examples are `com.samsung.tv.csfs`.
3. After verifying owner, architecture, UID and suitable runtime, use `app_operation_set_current_app(operation, targetApp)` for the main route and `vconf_set_str("db/appfw/home_appid", targetApp)` for the related Home preference. Verify both by readback. Helpers run with the developer SDK identity **UID 901** (not root).
4. Preserve exact per-TV originals off-device; on failure, restore and **verify** them. Do not synthesize stock-original values from another model. Restore must account for derived fields, other Home owners, unexpected missing/empty values and software updates.
5. Treat Smart Hub autostart and Samsung's derived startup/booting keys as **separate** behaviour from physical Home-key mapping. A value being writable/readable does not prove cold boot or foreground display.
6. Do not uninstall a currently assigned custom Home app before verified restoration.

Shared native libraries mentioned in source: `libbundle.so.0`, `libaul.so.0`, `libcapi-appfw-app-operation-tv.so.0`, `libvconf.so.0`, `libapp-context-manager-common.so`. Existence of these libraries or an exported setter only establishes *availability*, not safe platform semantics.

## Critical differences: why blind copy/paste is dangerous

| Dimension | Arn0 Q70B | CleanFrame LS03D | Couchroot S90D | Dant5 Clean Home current |
| --- | --- | --- | --- | --- |
| Home main route | Assign custom app | Assign custom app | Assign custom app | Assign custom app |
| Home preference | Set `home_appid` | Set `home_appid` | Set `home_appid` | Set `home_appid` |
| Smart Hub auto start | **Preserve baseline = 1** | Force `1` from recorded baseline | Original **0**, set **1** for boot | Force `1` in second step |
| Derived startup keys | Read and record; apply doesn't explicitly set them | Full snapshot, restore original values | Observed Samsung overwriting direct `startup_appid` edits; Home/auto matter | Validates changed/derived values, restores originals |
| Last-app autorun | Not changed by shown Home helper | Not changed by shown Home helper | Not the same dedicated feature | Explicitly disable `db/menu/app_booting`, then restore saved integer |
| Runtime | ARM32/SDK 901; assembly config must be inspected | **.NET 6** upstream | ARM32/SDK 901 native helper | Currently packaged **.NET Core 3.1** |
| Firmware support | One exact Q70B revision | One exact Frame revision | Studied specific S90D revision | One exact Q60B revision |
| Recovery | Exact baseline + rollback | Exact baseline + rollback | Early hard-coded restore example should **not be copied as-is**; later history notes recovery corrections | Device-bound baseline and transactional Undo, but guard blocks firmware-drift Undo |

**Do not copy Couchroot's example restore routine blindly:** its published native `Program.cs` uses fixed S90D target values and `auto_start=0` when restoring. Clean Home correctly needs the owner's **actual saved** original values, which could be different even on related models.

**Firmware caveat:** Clean Home currently enforces a single exact firmware in both the native control helper and read-only inspector; the Python host also insists on the exact model and firmware. Separate read-only discovery from write capability; never remove guards on native setters merely to test another model. Keep firmware-drift and loss-of-originals as explicit recovery contingencies.

**Transport caveat:** staging a native helper is a **TV operation**, even if the helper code only calls getters. A metadata-only check via supported LAN APIs is lower risk. Native getters on an unknown architecture or runtime can still fail or crash the helper.

## Additional cross-model evidence worth following up

- [CleanFrame PR #5](https://github.com/nthnclrk/CleanFrame/pull/5) demonstrates why *runtime compatibility* needs an explicit design. The Q60B reportedly had .NET Core 3.1.3 while the Frame had .NET 6. Their unmerged adaptation proposed a `netcoreapp3.1` assembly with `RollForward=Major`. **Do not assume** that a single major-roll-forward target is tested or works everywhere. Probe exact installed runtimes and choose a matching, separately tested bundled assembly where justified.
- [CleanFrame PR #2](https://github.com/nthnclrk/CleanFrame/pull/2) reports that on Q60B `tizen.application.launch("com.samsung.tv.coba.setting")` could indicate success but display **no UI** because it's an internal background component. Their unmerged approach launches an explicit `tizen.ApplicationControl` for the real Samsung UI, using `entry_point=smarthub_key` and, for Home, `switch_page=d/media.category`. This is a **candidate for a Samsung Home escape fallback**, not verified for Dant5 or the Frame.
- The same contributor observed hidden pre-launch with `document.hidden` and paused `requestAnimationFrame`, so preloaded photos and initial compositor transitions might fail silently on cold boot. Prefer a real physical boot test over browser-only rendering assurances.
- A cached DU7660 README reports the distinction between `entry_point=smarthub_key` (physical Home) and `entry_point=cold_booting` with background launch. Do not assume the code is still available or its claimed hotfix works; add tests for both launch modes.
- Couchroot's S90D case notes `db/appfw/startup_appid` alone did **not** force startup. Tests of **Home**, **foreground cold boot**, **standby wake** and **restore** must remain separate.
- An unexpected original empty/missing key is not equivalent to stock Samsung Home. Refuse to apply if exact state cannot be preserved and restored. Do not quietly invent defaults.
- Despite overlapping implementations, the 2022 Q70B, 2024 Frame and 2024 S90D represent different physical device evidence. This does **not** prove that changing Home is portable to Tizen 5/7/8/10 or ARM64.

## Recommended architecture for Codex

**Stage A: metadata-only compatibility check.** Explicit user-directed scan of local TV data, read model/firmware/architecture and supported developer API/runtime metadata. No signing, root, restart, apps install/uninstall, settings writes or native helper execution. Redact unique identifiers and local IP from shareable reports.

**Stage B: optional getter-only probe.** On owner consent and a compatible runtime/architecture, launch a minimal bounded read-only helper through reviewed developer transport. Never include write imports in this executable; report UID, firmware, runtime, native exports, typed keys, main route, stock-Home app ID and boot eligibility. Local report review before any share. Be clear that helper execution changes temporary staging files even though TV settings are not written.

**Stage C: profile-based native write.** A *specific model + firmware + runtime + ABI + SDK identity* is allowed to apply only after actual device evidence, a validated per-device original backup with export/import, and a tested Undo path. Separate grades: metadata-visible / getter-compatible / Home-key owner-confirmed / cold-boot confirmed / Undo confirmed. No Tizen-version blanket allowlist.

**Stage D: safe in-TV escape.** Test both direct stock Samsung Home launch and a targeted ApplicationControl on the exact firmware. Make a no-PC, TV-remote-accessible fallback if reliable. Do not use the redirected physical Home button as fallback guidance if the stock Home launch failed.

**Stage E: fault-injection testing.** Test original autostart 0 and 1, last-app 0 and 1, two different Home IDs, derived startup-key changes, firmware drift after apply, missing or tampered baseline, unsupported runtime/ABI/UID, partial write, failed rollback, hidden background launch, Home event and cold boot with distinct entry points, and physical off/on/Undo. No simulator result counts as a hardware pass.

## What should and should not be merged for 31 October

- **Suitable for the preview**: this report, source-only research branch, offline mock tests, owner-run nonwriting compatibility reporter (once vetted), honest compatibility and volunteer instructions.
- **Not suitable to generalise automatically**: removal of firmware checks, accepting any Tizen 9 TV, writing a Home mapping on a stranger's TV based on these projects, treating successful setter readback as proof of physical Home/boot/Undo.
- **Dependency warning**: do not ship copied native control source or sample original settings in the release bundle. Preserve ownership and attributions. Keep the live Q60B experience unchanged.

## Codex tasks from this research

1. Compare these pinned source snapshots line-by-line with `tools/home-control/{NativeControl,Policy,SetupPolicy,StartupOption}.cs` and `tools/home-inspection/HomeInspection.cs`; record functional differences, separating necessary compatibility work from different coding styles.
2. Inspect [CleanFrame PR #2](https://github.com/nthnclrk/CleanFrame/pull/2) and [#5](https://github.com/nthnclrk/CleanFrame/pull/5) as **unmerged** research, not automatically production-ready patches.
3. Build getter-only cross-model diagnostic capability without weakening any current write guard; if this needs TV access, prepare owner steps and stop.
4. Make Home escape robust on the actual reference TV; prepare a non-invasive test script and explicit failure/rollback instructions.
5. Produce a model/firmware/runtime matrix from evidence and a clear GO/NO-GO separate for (a) ordinary app preview, (b) read-only compatibility reporter, and (c) native Home overwrite on each exact new device.
6. Review third-party licensing, the public source checker and package inclusion rules; keep this `research/` directory excluded from runtime packages.

See [release-readiness issue #13](https://github.com/Dant5/clean-home-tizen/issues/13) for the wider launch checklist.
