# Clean Home for Samsung Tizen

A quiet home screen for Samsung TVs: photographic backgrounds, a clock, a glass dock and the apps **you** choose. Based on [Clean Home](https://github.com/chaosmanage/samsung-tv-launcher) and Nathan Clark’s CleanFrame, with the existing visual design retained.

[![Tests](https://github.com/Dant5/clean-home-tizen/actions/workflows/ci.yml/badge.svg)](https://github.com/Dant5/clean-home-tizen/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Public preview — Tizen 6.5 / Q60B tested.** The launcher core has been used on a 2022 Samsung Q60B. The new first-run picker and long-press controls pass browser tests, including Chromium 85; they are not yet independently confirmed with a physical TV remote. Other models and firmware need community testing. See [compatibility and known limits](docs/COMPATIBILITY.md).

![Example Clean Home layout](docs/images/home-example.jpg)

*Example arrangement. A fresh installation starts with one “+” tile, without preselected favourites.*

## Getting started

1. Download the **unsigned `.wgt`** from [Releases](https://github.com/Dant5/clean-home-tizen/releases), and compare its SHA-256 with `SHA256SUMS`.
2. Follow [installation](INSTALL.md) to enable Developer Mode and let Apps2Samsung sign/install it with **your own** Samsung profile. Alternatively, use your own Tizen Studio certificate profile.
3. Open Clean Home from the TV’s Apps list. Select **+**, choose an installed app, and repeat. Up to nine apps fit the existing scrolling dock.

A short press of the centre/Select button opens an app. Hold Select for about **two-thirds of a second** to replace that app; release, then choose its replacement. Back cancels a picker without changing anything. Settings → Apps on Home provides reordering and removal. Existing saved favourites are preserved on upgrade and receive no extra “+” tile.

![A fresh installation starts with one add tile](docs/images/first-run.jpg)

<details>
<summary>See the app picker</summary>

![Choose from the installed apps on your own TV](docs/images/app-picker.jpg)

</details>

The original 16:9 design scales to the TV’s application viewport, keeping the same proportions at 720p, 1080p and 4K. Non-16:9 preview windows use letterboxing. Physical panel size does not require a separate layout. Firmware and app-launch support still vary by model.

This is an independent launcher app. Installing the download does **not** remap the physical Home button or guarantee power-on startup. Native Home/startup has worked on the reference Q60B through a separate, firmware-specific developer configuration; it is advanced research, not a portable one-click feature. [Read that boundary first](docs/NATIVE-HOME.md).

The original Samsung Home, Settings and HDMI/input selector remain accessible. Existing applications, accounts and Moonlight pairings are not reinstalled or cleared. There is no root requirement, debloater or always-running Home watcher in the widget.

## Preview and build

Requirements: Node 22+, Python 3.10+ with venv/pip support. On Debian/Ubuntu, install `python3-venv` if the venv command reports missing ensurepip.

```sh
npm ci
python3 -m venv .local/venv
.local/venv/bin/python -m pip install -r requirements-build.txt
npx playwright install chromium
npm run dev:public
```

Open the localhost URL printed by the preview. Arrows, Enter and Escape correspond to the remote. A desktop browser cannot discover a television’s apps; installed-app choices require the TV, while tests supply a mock inventory.

```sh
npm run check
npm run check:device
npm run check:onboarding
npm run check:python
npm run package
```

The result is `dist/CleanHome-Q60B-unsigned.wgt`. It includes public fonts and licences, without device IDs, signing keys or a personal app profile. An unsigned widget needs local signing before a consumer TV will install it. [Development and full tests](CONTRIBUTING.md) · [release process](docs/RELEASING.md).

## Support and privacy

Use the bug or compatibility-report forms in [Issues](https://github.com/Dant5/clean-home-tizen/issues). Include model, firmware and app version; omit serial numbers, DUIDs, addresses, certificates, tokens and account screens. See [privacy](PRIVACY.md), [security reports](SECURITY.md) and [removal/recovery](INSTALL.md#removal-and-recovery).

Bing daily pictures are optional and can be turned off. Fifteen credited wallpapers work offline. Weather is off by default. No analytics, camera or microphone feed is included.

Original code is MIT. Fonts, photographs and service marks retain their own terms. Keep [LICENSE](LICENSE), [third-party notices](THIRD_PARTY_NOTICES.md) and the adjacent asset licences. [Upstream credits](docs/UPSTREAM.md).
