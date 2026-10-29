# Clean Home Tizen public source

Preserve the Clean Home/CleanFrame design, original MIT notices and third-party licences. Runtime JavaScript must parse as ES5 and work with Chromium 85. Keep the exact application/package identity when updating an existing installation.

Fresh installations start with a single + tile and no favourite assumptions. Choosing an app appends it and leaves one + until capacity. Holding Select replaces the selected tile; short Select launches only on release. Preserve saved favourites, appearance and manual bindings on upgrade. Treat picker cancellation, save failure, repeat keys, blur and suspend as important regression cases.

Run npm test and packaged-widget checks after relevant changes, using current Chromium and Chromium 85. The tests use a mock Tizen boundary and never require a TV. Regenerate/check cached shading when its inputs change. Report which engine, artifact and actual hardware were tested; do not infer visual success from a launch callback.

The normal widget must not root, remove/disable packages, reset Smart Hub, change firmware/update policy, modify protected services, install a watcher or overwrite other app data. Native helper sources are separate advanced research; inspect their exact scope and baseline/rollback rules before any change. A firmware guard is not model compatibility proof. Do not connect to, install on or modify a television without its owner's task-specific authorisation.

Do not add or publish signing keys, passwords, personal app profiles, DUIDs, addresses, recovery snapshots, proprietary fonts, recordings, vendor firmware or decompiled proprietary code. Keep local work in ignored .local/. Review explicit staged paths/diffs and run secret checks. Release artifacts are unsigned, generic and reproducible; publishing a repository/release is a separate human approval step.
