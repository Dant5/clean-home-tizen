<div align="center">

# Clean Home

### Make your Samsung TV feel like yours.

A photo. A clock. Your favourite apps. A beautifully simple home screen.

**No root. Your apps stay installed. Samsung Home stays available.**

**[⬇ Download the preview](https://github.com/Dant5/clean-home-tizen/releases/tag/v1.4.2-preview.1)** · [Install guide](docs/INSTALL.md) · [TV support](#tv-support)

</div>

![Clean Home: a photograph, clock and glass app bar](docs/images/home-example.jpg)

*Your apps, your choice. A fresh install starts with a single **+**.*

## What you get

- **A clean home screen** with daily photos, a clock and a glass app bar.
- **Your favourite apps**, including sideloaded apps. Pick up to nine.
- **Your settings stay yours.** Shortcuts leave existing apps, accounts and pairings alone.
- **Simple remote controls.** Arrows to move. Centre button to choose. Back to return.

### Home button + automatic startup

The optional **[Home Setup tool](docs/NATIVE-HOME.md)** can make Home and power-on open Clean Home, without root or a PC left running. It includes Undo and keeps Samsung Home accessible.

This setup is **experimental** and currently accepts **QA55Q60BAWXXY / T-NKLBUABC-1720.7 only**. Installing the TV app alone keeps Samsung Home in charge; open Clean Home from Apps.

## TV support

Targets **Tizen 5.0 and newer**. Our real-TV reference is a **2022 Samsung Q60B**; other models need confirmation. The layout scales to fit your screen.

![TV support: browser checks pass on Tizen 5.0–10.0; Q60B on 6.5 is the only real-TV reference](docs/images/compatibility.svg)

**Feedback wanted!** Tried your TV? Open **Settings → Samsung → Share TV report**, review the details and press **Send**. No phone or account needed. [What gets shared](docs/TV-REPORTS.md).

## Install it

**🛠️ Difficulty: 3/10.** No coding. You need a computer on the TV’s home network and a Samsung account.

1. **Get the app and installer.** Download the **`-unsigned.wgt`** file from [Clean Home Releases](https://github.com/Dant5/clean-home-tizen/releases/tag/v1.4.2-preview.1), then open [Apps2Samsung](https://github.com/Apps2Samsung/Apps2Samsung/releases).
2. **Enable Developer Mode.** On the TV, open **Apps**, enter **1 2 3 4 5**, switch Developer Mode **On**, enter your **computer’s local IP address**, then restart. [Find the address](docs/INSTALL.md#2-find-your-computers-address).
3. **Install the file.** In Apps2Samsung, select your TV → **Install a file…** → choose the `.wgt`. Follow the Samsung sign-in and certificate prompts.
4. **Make it yours.** Open **Clean Home** from the TV’s Apps screen. Choose **+**, then an app.

**[Full step-by-step guide and fixes →](docs/INSTALL.md)**

## Use it

| Want to… | Do this |
| --- | --- |
| Add an app | Choose **+**. |
| Open an app | Press the remote’s centre **OK/Enter** button briefly. |
| Change a shortcut | Hold **OK/Enter** for about a second, release, then choose another app. |
| Reorder or remove shortcuts | **Settings → Apps on Home**. |
| See everything else | **All apps**, at the top right. |

Photos, appearance, TV settings and HDMI inputs are under **Settings**. **Back** cancels. Removing a shortcut keeps the app installed.

<details>
<summary>Why are some icons coloured?</summary>

Recognised apps use matching monochrome logos. Others use their installed icon, or initials if no icon is available. For a uniform text-only look: **Settings → Layout → App display → Text**.

</details>

## Help & credits

[Get help](https://github.com/Dant5/clean-home-tizen/issues) · [Uninstall](docs/INSTALL.md#updates-and-removal) · [Privacy](docs/PRIVACY.md)

Based on **[Clean Home by chaosmanage](https://github.com/chaosmanage/samsung-tv-launcher)**, built on Nathan Clark’s **CleanFrame**. The original look is preserved. [Full credits](docs/UPSTREAM.md) · [MIT licence](LICENSE) · [Third-party notices](docs/THIRD_PARTY_NOTICES.md).

<details>
<summary>For developers</summary>

[Build & contribute](.github/CONTRIBUTING.md) · [Test results](docs/TEST-RESULTS.md) · [Release process](docs/RELEASING.md)

</details>
