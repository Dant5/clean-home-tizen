# Make Clean Home your Home screen

**Home and power-on can open Clean Home without root.** This is step 5 of the [main installation guide](INSTALL.md#5-make-it-your-home-screen). The Home tool is included in the Clean Home Setup bundle, saves the original preferences and includes Undo. Samsung Home stays accessible inside Clean Home.

## Supported TV

| TV and software | Home and power-on |
| --- | --- |
| **QA55Q60BAWXXY / T-NKLBUABC-1720.7**, ARM32, developer SDK UID 901 | Underlying method verified on our TV. New guided tool is **experimental** and needs its own physical-TV rehearsal. |
| Other models or software | Check TV and Send compatibility report are available; Home/settings changes remain blocked pending a reviewed profile. |

An OS version alone does not establish native compatibility. Please do not remove the firmware guard to try another TV. [Send a TV report](TV-REPORTS.md) so we can prioritise more models.

## Before you start

1. To change Home, [install Clean Home](INSTALL.md) using your own Samsung certificates and open it once. **Check TV and reports work without the widget installed**, so an installation failure does not block diagnostics.
2. Use the same computer whose address is entered as **Host PC IP** in the TV’s Developer Mode.
3. Close Apps2Samsung so only this tool uses the developer connection. Keep the TV on.

## Set it up

1. **Windows:** in the extracted **CleanHome-Setup-Windows-preview.zip**, open **home-setup/CleanHome-Home-Setup.exe**. Python is included; no installation or administrator account is needed. If the TV app is already installed, the smaller **CleanHome-Home-Setup-Windows-experimental.zip** contains the same tool.
2. **Linux:** in **CleanHome-Setup-Python-preview.zip**, run **home-setup/START-LINUX.sh** with Python 3.11 or newer. Already installed? The smaller **CleanHome-Home-Setup-experimental.zip** contains the same tool. Python users on Windows can use **START-WINDOWS.cmd**. No extra Python packages or Tizen Studio are required. The tool opens a local browser page.
3. Enter the **TV’s** local address, found in **Settings → General → Network → Network Status → IP Settings**. Choose **Check TV**. Unlisted models continue to the compatibility results; they are not rejected before diagnostics.
4. Read the confirmation, tick the box and choose **Use Clean Home**. The tool saves and verifies the original preferences before making a change. Wait for its confirmation.
5. Press Home on the physical remote. It should open Clean Home. Open Samsung Home from Clean Home’s top row to check the original interface is available. Turn the TV off normally, wait 30 seconds, then switch on and check startup.

Keep the **recovery folder** shown by the tool, including when moving computers. On Windows it is in your user’s local application data under **CleanHome/recovery**; on Linux under **~/.local/share/CleanHome/recovery**. These files belong to that TV. They are not backups of your apps or accounts. Do not upload them in a public issue.

Close the setup terminal when finished. No PC, online service, Home Assistant automation or always-running watcher is needed for normal Home/startup behaviour.

## Help add your model

Choose **Check TV** on any Samsung model. The tool checks TV identification, Developer Mode, platform metadata, temporary helper execution, account/architecture and each Home/startup getter independently. Getter failures do not hide later independent results; dependent checks are marked **skipped**, not passed.

A fixed getter-only helper may be staged temporarily and cleaned up. This does not change Home, startup, applications, picture or sound settings. It refuses root and unsupported architectures. Other non-root account classes can try getters, which report their permission failures independently; Home writes still require the reviewed SDK account and profile. It does not try unverified Home writes or cycle through setter methods.

Review **Compatibility results**, then choose **Send compatibility report**. No phone or account is needed. **Save report** makes a local JSON copy. Reports include model/software and fixed capability/error categories; no address, DUID, serial, app inventory, original settings or raw output. After an attempted supported setup/Undo, its confirmed/unknown outcome is included too.

Successful reads help develop a profile; they do not prove that setters or rollback work on that firmware. A new Home profile still needs bounded validation and a real-TV rehearsal before general release. [Report details](TV-REPORTS.md).

## Undo or uninstall

1. Run the tool on the same computer, enter the TV’s address and choose **Check TV**.
2. Tick **Restore this TV’s original Home and startup preferences**, then choose **Undo setup**.
3. Wait for confirmation. Press Home on the physical remote and check Samsung Home opens. Check a normal off/on cycle too.
4. You may now uninstall Clean Home through Apps. Removing the TV app alone does **not** restore external Home preferences.

If setup is interrupted, keep the TV and computer on. Open the tool again and use **Check TV**, then **Undo**. The tool records uncertain operations and does not automatically retry a change. If Undo cannot confirm success, stop and report the visible error; keep the recovery folder. If the original computer is gone, recover that folder before attempting native changes. A sample configuration cannot replace your TV’s originals.

A TV software update may need an updated setup/Undo profile. Keep Clean Home installed until restoration is confirmed. If the developer connection fails, check Host PC IP, close Apps2Samsung and check whether the computer's firewall is allowing the tool on your private home network. Router port forwarding is not needed.

## What changes

The rootless helper changes Samsung’s main/Home application assignment, the named Home preference, Smart Hub autorun and the integer Autorun Last App preference. Autorun Last App is disabled so a previously watched app does not bypass Clean Home. Derived Home fields are checked against the saved original configuration. Undo restores the complete saved Home snapshot and the original Last App integer.

The tool checks the exact model over the TV’s local API and the exact firmware, ARM32 architecture and SDK UID inside the native helper. It refuses root. Temporary helper files are checksum-verified, run once and removed, with explicit completion and cleanup checks. The host uses a device-bound recovery record and permits only the fixed inspect, setup and Undo actions. It does not provide a general command console.

No apps are removed, reinstalled or updated. There is no rooting, firmware flash, protected-package removal, Home watcher, update-policy change, or picture/sound modification. The ordinary `.wgt` does not perform native setup by itself.

## For developers

Sources: `tools/home-setup/`, `tools/home-control/` and `tools/home-inspection/`. Build the companion with `python3 scripts/build-home-setup.py --dotnet PATH_TO_DOTNET`. The helper targets the TV’s existing .NET Core 3.1 runtime; never install or upgrade a TV runtime to run it.

The transport adapts [AeroTizen’s](https://github.com/helalaou/AeroTizen) bounded SDK staging, with its MIT notice and pinned source record retained. It does not include AeroTizen’s root providers or watcher installation. Native policies have fake-platform failure and recovery tests; the host has fake-device, identity, snapshot, transport and local-browser request tests. [Test evidence](TEST-RESULTS.md).

[tizen-sim](https://github.com/lucaskfp/tizen-sim) is useful for versioned Chromium, Tizen APIs, remote keys, privileges and app lifecycle. It does not implement Samsung’s native Home assignment, firmware or standby boot path. Simulator passes cannot verify native setup on additional TVs.

Research references: [arn0-tv’s Q70B guide](https://github.com/NelsonEU/arn0-tv/blob/main/docs/setup-tv.md), [Clean Home](https://github.com/chaosmanage/samsung-tv-launcher), [Samsung multitasking](https://developer.samsung.com/smarttv/develop/guides/fundamentals/multitasking.html). Other projects’ model reports guide investigation; they are not hardware verification for this tool.
