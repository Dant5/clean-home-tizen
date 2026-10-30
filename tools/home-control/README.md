# Native Home control for this Q60B

Separate, short-lived .NET helper for the owner-authorised native investigation. It is not part of the signed web widget and installs no service or watcher. It runs through the existing developer connection as SDK UID 901, without root. It refuses other process architectures, identities and firmware families; the exact required firmware line is `Version=T-NKLBUABC-1720.7;`.

The native Home operation and Home id are assigned through `app_operation_set_current_app` and the named vconf preferences. This is undocumented Samsung TV behaviour, not a public web-app capability. The firmware guard is a refusal check, not proof of compatibility by itself. Actual Q60B apply, readback and restoration evidence is recorded in [the compatibility record](../../docs/COMPATIBILITY.md).

## Scope and recovery

An immutable private baseline records the original main operation, four string preferences and Smart Hub autorun integer. A separate immutable baseline records the subsequently discovered integer `db/menu/app_booting` (Samsung Autorun Last App). Preserve the complete recovery directory outside Git. Never substitute the example values from another television. The original last-app backup may legitimately contain Clean Home; it is not evidence that the original Home operation was already replaced.

Actions take a baseline JSON file:

- `verify`: compare against the complete original snapshot; no writes.
- `apply-home`: require the original state and an installed, boot-eligible launcher, assign only main/Home id and restore unrelated startup values if Samsung derives changes.
- `apply-boot`: require the previously applied Home state, enable Smart Hub autorun and let Samsung derive startup ids. Preserve the original first-screen preference. The TV normally updates its last-app backup while running; only the saved backup, saved startup id or our own id are accepted for that volatile field.
- `restore`: restore the complete original snapshot without requiring the launcher to remain installed; refuse an unrecorded changed autorun value.
- `restore-boot`: restore the original snapshot after recorded boot enablement. The private host runner requires a matching boot intent and immutable-baseline checksum before invoking it.

Every change is followed by readback. A failure attempts exact restoration of the pre-action snapshot and reports incomplete rollback explicitly. The SDK file lock prevents simultaneous controller instances. It is an inert file, not a running process. Readback proves the observed settings, not on-screen rendering or every future wake.

The additional `verify-option`, `disable-last-app` and `restore-last-app` actions operate only on `db/menu/app_booting` with its recorded original integer as an explicit argument. Disable requires native Home and Smart Hub autorun already configured; exact restore is rehearsed before leaving it off. The private runner verifies that this second baseline and the matching controller are in the independently checked recovery archive. Restore this option as well as the original Home snapshot when undoing native setup.

The helper has no package install/remove, generic settings, root, firmware, service-control, picture/sound or app-data APIs. Temporary staging is checksum-verified and cleaned by the separately reviewed host runner. A developer-channel error can occur after command evaluation, so the runner uses a bounded callback verified against the TV peer. An unknown execution outcome must be investigated with the read-only probe before another write.

## Build and offline policy checks

```sh
dotnet build tools/home-control/HomeControl.csproj -c Release
dotnet run --project tools/home-control/PolicyTests.csproj -c Release
```

The device target is the TV's existing .NET Core 3.1; the build emits expected legacy-runtime warnings. Do not install or upgrade a TV runtime. Policy tests use a fake platform under .NET 10 and make no native calls or network requests. They cover exact recovery, volatile backup transitions, drift refusal, ineligible/missing apps, silent mismatches and failures after mutation. Generated files stay under ignored `.local/native-control/`.

The optional [Home Setup companion](../../docs/NATIVE-HOME.md) now supplies the public transport and guided inspect/setup/Undo flow. `apply-all` combines the existing Home, autorun and Last App policies into one guarded transaction; `restore-all` verifies full restoration. Recovery originals, addresses, certificates and private execution receipts stay outside Git. The companion is experimental and remains restricted to the exact verified model/software; its new end-to-end flow needs a physical-TV rehearsal. Restore the native baseline **before uninstalling Clean Home**. Samsung Home remains installed and can be launched through Clean Home's Samsung Home control.

Native snapshot/readback ideas are adapted from AeroTizen by Hamza El Alaoui, MIT, reviewed at `c4b649b4fa22a43e19842f0f6d52acdfa69cc1d3`. Retain [its licence](../../vendor/aerotizen/LICENSE), the root licence and [third-party notices](../../docs/THIRD_PARTY_NOTICES.md).
