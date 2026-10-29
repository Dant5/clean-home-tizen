# Native Home and power-on startup

The ordinary web application can be installed and opened from Apps without changing the TV’s native Home configuration. It cannot intercept the Home button itself. The Samsung Home shortcut opens Samsung’s interface; Back closes a launcher panel and stays on its Home view.

A separate rootless developer method worked on the reference QA55Q60BAWXXY / T-NKLBUABC-1720.7. It changes Samsung’s native main/Home assignment, Smart Hub autorun and the integer Last App preference. It uses the existing SDK developer identity, not an always-running watcher or a delayed Home Assistant launch.

**That configuration is not portable or automatically installed by this release.** Source is included under `tools/home-inspection/` and `tools/home-control/` for review and qualified adaptation. The device transport and per-TV recovery snapshots from the reference installation are private and are not usable as another owner’s installer. There is no public “make this Home” command in this preview.

The native sources check the process architecture, SDK UID and exact expected firmware line. They do not independently prove the TV model is compatible. Never weaken a guard to try another firmware. Read/query first, preserve immutable originals outside Git, establish a working restoration path and require the device owner’s explicit approval before any native write.

If native configuration has been applied, restore both the original Home snapshot **and** the original Last App integer, verify Samsung Home works through the physical remote, then uninstall. An app uninstall does not undo those external preferences. The reference restoration was rehearsed, but a different device needs its own baseline; example values are not a backup.

Samsung Home and full Settings must remain accessible. No rooting, firmware patch, protected-package removal, Home watcher, update-policy change or picture/sound modification is included. Read the source’s scope and fake-platform tests before attempting further work.

Research references: [arn0-tv’s Q70B guide](https://github.com/NelsonEU/arn0-tv/blob/main/docs/setup-tv.md), [Clean Home](https://github.com/chaosmanage/samsung-tv-launcher), [Samsung multitasking](https://developer.samsung.com/smarttv/develop/guides/fundamentals/multitasking.html). Different models’ results are research references, not compatibility evidence for this release.
