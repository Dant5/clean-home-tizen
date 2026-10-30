# Changelog

## 1.4.3 preview

- Lets other Samsung models run setup diagnostics and send a compatibility report instead of being rejected at the model check.
- Checks connection, native runtime, account/architecture and each Home/startup getter independently, with fixed failure codes and skipped stages.
- Adds review, one-button send, local save, duplicate suppression and setup/Undo outcome reporting. No raw settings, app IDs, addresses or device identifiers are uploaded.
- Keeps Home writes restricted to reviewed profiles, with the original-setting backup and Undo unchanged.

## 1.4.2 preview 2

- Makes Home-button replacement and automatic startup part of the main setup guide.
- Bundles the unsigned TV app, existing Home tool, offline four-step guide and checksums in one download for Windows or Python/Linux.
- Keeps the TV app and native helper behaviour unchanged from preview 1; the same compatibility guard, saved originals and Undo apply.

## 1.4.2 preview 1

- Adds a visual compatibility chart, separating browser checks from real-TV evidence.
- Adds **Settings → Samsung → Share TV report** for success and problem reports.
- Sends basic TV details only after an explicit button press; no phone or account needed. Received reports stay private. Phone/GitHub reporting remains optional.
- Keeps accounts, app lists, addresses, unique device identifiers and raw logs out of shared reports.
- Adds an experimental optional Home Setup companion, with original-setting backup and Undo, restricted to the verified Q60B model/software. The TV app alone preserves Samsung Home.
- Adds tizen-sim platform checks, alongside the existing eight-engine browser matrix.

## 1.4.1 preview

- Adds a Tizen 5.0 minimum and compatibility work for older and newer TVs.
- Keeps the original spacing on older TV browsers.
- Gives older browsers an abortable daily-photo request.
- Adds checks for the browser generations used by Tizen 5.0 through 10.0.

## 1.4.0 preview

- Choose your own apps: a fresh install starts with **+**. Add up to nine shortcuts.
- Hold **Select** to replace a shortcut.
- Existing favourites and settings are kept on update.
- Keeps the original Clean Home photo, glass app bar and clock.
- Adds an unsigned download, installation guide and compatibility reporting.

[TV compatibility](COMPATIBILITY.md) · [Developer test results](TEST-RESULTS.md)

## 1.3.9

- Improves startup responsiveness by preparing the background shading in advance.

Based on Clean Home and CleanFrame. See [credits](UPSTREAM.md).
