# Read-only native Home inspection

This is a getter-only diagnostic, separate from the normal signed widget. On 28 October 2026 its netcoreapp3.1 build successfully ran on the actual Q60B as SDK UID 901, returned the original Home/startup preferences and boot eligibility, and confirmed temporary staging cleanup. No transport or installer is included in this public source directory. The installed Clean Home widget does not contain it.

The getters adapt [Clean Home's native helper](https://github.com/chaosmanage/samsung-tv-launcher/blob/57415fdf5ffc2013b66bc98aca94e0963e0888be/scripts/native-home/Control.cs), MIT, copyright 2026 Nathan Clark; retain the root [licence](../../LICENSE) and [notices](../../docs/THIRD_PARTY_NOTICES.md). Upstream applies a default Home assignment on a different, firmware-guarded 2024 TV. **Its write functions and SDB command-injection transport are excluded here.**

`--describe` prints scope without invoking native functions. `--query` refuses non-ARM32 execution, unverified firmware and any UID other than the reference SDK UID 901. Its intended firmware is owner-reported/read-back T-NKLBUABC 1720.7. It reads the default main app operation, four Home/startup string keys, the existing autorun integer and our own app's boot-eligibility flag. The `aul_svc_set_operation` import initialises a new in-memory query bundle; it does not change the system's default application. Each query reports an error when unavailable. There are no system setters, file writes, process launches, network requests, app-private-data reads or restore operations.

Build with a trusted .NET SDK; generated intermediates and outputs stay under ignored `.local/`:

```sh
dotnet build tools/home-inspection/HomeInspection.csproj -c Release
dotnet .local/native-inspection/bin/Release/netcoreapp3.1/CleanHomeReadOnlyInspection.dll --describe
```

The project builds **netcoreapp3.1 and net6.0 separately**. The 3.1 target follows [arn0-tv's native query project](https://github.com/NelsonEU/arn0-tv/blob/main/native/Query.csproj), reported working on a 2022 Q70B/Tizen 6.5. Samsung's [TV Extension 6.5 release history](https://developer.samsung.com/smarttv/develop/tools/tv-extension/release-history.html) also lists .NET Core 3.1; the 2024 Clean Home reference uses .NET 6. Both are legacy runtimes and produce NETSDK1138 warnings. Outputs are separated by target under ignored `.local/native-inspection/bin/Release/`. Choose only after reading the actual TV runtime; never install/upgrade a TV runtime for this tool. Host `--describe` can use `DOTNET_ROLL_FORWARD=Major` for offline checks, but do not use that setting to hide a device runtime mismatch. The netcoreapp3.1 target was executed through the separately reviewed developer runner; no root attempt or runtime upgrade occurred.

Before any eventual device query, separately establish the runtime, library signatures, developer execution path and read permissions. The upstream `run.py` injects a command through a package-name field even for queries; review its staging/execution effects explicitly rather than calling it an ordinary inventory read. Do not relax guards to get past errors. The owner's 28 October clarification allows reconsidering native Home/startup changes; this keeps the method in scope for investigation. The separate [native controller](../home-control/README.md) now implements scoped apply/restore using the saved actual baseline; this getter-only tool still contains no setters.

See [startup findings](../../docs/NATIVE-HOME.md). This tool is not required for the REST startup candidate.

## Bounded startup-component inspection

`--startup-strings` applies the same device guards, then reads at most 32 MB from each of three named startup components. It returns selected startup/Home strings and preference names, with bounded output, plus selected integer/boolean getters. It neither copies complete vendor binaries into Git nor changes them. On this Q60B, `app-boot-manager` and `libapp-context-manager-common.so` were readable; the guessed `app-context-manager` executable path was absent. The latter library names an “Autorun Last App option is OFF” branch and `db/menu/app_booting`; its actual integer getter returned **1**, while its boolean getter refused the type. This led to the separately backed-up integer option in the native controller. Strings identify a candidate mechanism; the subsequent reversible toggle and real wake tests supply behavioural evidence. No full decompilation or kernel patch is claimed.
