# Install and use Clean Home

**Install Clean Home, then make Home and power-on open it.** No root. Your apps stay installed and Samsung Home stays accessible. The setup bundle includes the TV app, Home tool and an offline guide.

**[Get Clean Home Setup](https://github.com/Dant5/clean-home-tizen/releases/tag/v1.4.3-preview.1)**

Home replacement is experimental and currently accepts **QA55Q60BAWXXY / T-NKLBUABC-1720.7 only**. Other Samsung models can install the app and run **Check TV** to send compatibility results; their Home settings are left alone.

## Before you start

You need:

- A Samsung TV with **Tizen 5.0 or newer**. Developed on the **2022 Q60B**; [other models are unconfirmed](COMPATIBILITY.md).
- A computer on the same home network as the TV.
- A Samsung account for the installer’s certificate setup. A certificate lets the TV accept the app.

## 1. Download Clean Home Setup

1. Open [Clean Home Downloads](https://github.com/Dant5/clean-home-tizen/releases/tag/v1.4.3-preview.1) → **Assets**.
2. Choose your bundle below, extract the whole ZIP, then open **START-HERE.html**. The TV app and Home tool are already inside.
3. Download and open [Apps2Samsung](https://github.com/Apps2Samsung/Apps2Samsung/releases). It handles Samsung sign-in and signing; choose its desktop app with **Install a file…** support.

| Computer | Clean Home download | Apps2Samsung download |
| --- | --- | --- |
| Windows | **CleanHome-Setup-Windows-preview.zip**; Python is included. | Desktop **`.msi`**. |
| Linux | **CleanHome-Setup-Python-preview.zip**; needs Python 3.11 or newer. | Desktop **`.AppImage`**, `.deb` or `.rpm`. |
| Mac | Standalone **`-unsigned.wgt`** for installing the TV app. The Home setup has not been tested on macOS. | **`macos-arm64.dmg`** for Apple silicon, **`macos-x64.dmg`** for Intel. |

Already installed Clean Home? You can use the **Home-Setup** download alone. The source-code ZIP is for developers.

<details>
<summary>Optional: check your download</summary>

The same release includes `SHA256SUMS`. Compare the checksum for your downloaded file using `Get-FileHash` in Windows PowerShell or `shasum -a 256` / `sha256sum` on Mac/Linux. If they differ, download again before installing.

</details>

## 2. Find your computer’s address

You need **your computer’s local IPv4 address** for the TV’s setup.

| Computer | Where to find it |
| --- | --- |
| Windows | **Settings → Network & internet** → connected Wi-Fi/Ethernet connection → **Properties → IPv4 address**. |
| Mac | **System Settings → Network** → connected Wi-Fi/Ethernet connection → **Details → TCP/IP → IP address**. |
| Linux | Connected Wi-Fi/Ethernet connection’s **Details → IPv4 address** in network settings. |

Use the home-network connection, rather than a VPN or virtual adapter. More help: [Windows](https://support.microsoft.com/en-us/windows/experience/connectivity-networking/essential-network-settings-and-tasks-in-windows) · [Mac](https://support.apple.com/en-gb/guide/mac-help/mh14129/mac).

## 3. Enable Developer Mode on the TV

1. Open **Apps** from Samsung Home.
2. Enter **1 2 3 4 5** with the remote’s number buttons or on-screen number keypad. Some models need **Apps → App Settings** first.
3. Switch **Developer Mode** to **On**.
4. In **Host PC IP**, enter the **computer’s address from step 2**.
5. Select **OK** and restart as prompted. Reopen Apps to check Developer Mode is on.

Developer Mode allows app installation; it does not root the TV. If the window does not appear, see [Samsung’s illustrated guide](https://developer.samsung.com/smarttv/develop/getting-started/using-sdk/tv-device.html). A factory reset or service menu is not needed.

## 4. Install Clean Home

1. In **Apps2Samsung**, select your TV and wait for it to be ready. Check the model: a Samsung soundbar can also appear.
2. Choose **Install a file…** and select the Clean Home `.wgt`.
3. Follow the Samsung sign-in and certificate prompts using your own account. For an update, reuse your existing signing profile.
4. Wait for installation to succeed, then open **Clean Home** from the TV’s **Apps** screen.

You should see a photograph, clock and **+** tile. An existing installation keeps its saved apps.

## 5. Make it your Home screen

1. Close Apps2Samsung. Keep the TV on and use the same computer listed as Host PC IP in Developer Mode.
2. In the extracted bundle, open **home-setup/CleanHome-Home-Setup.exe** on Windows, or **home-setup/START-LINUX.sh** on Linux with Python 3.11 or newer.
3. Enter the **TV’s** address from its **Network Status → IP Settings** screen. Choose **Check TV**. This works on other Samsung models too and runs independent capability checks using temporary diagnostic files. Home/settings are not changed by the checks.
4. If supported, read the confirmation, tick the box and choose **Use Clean Home**. Original Home/startup preferences are saved and verified before a change.
5. Press **Home** on the physical remote, then try a normal off/on cycle. Clean Home should appear. Choose its **Samsung Home** button to check the original screen is available.

Keep the recovery folder shown by the tool. **Use Undo before uninstalling Clean Home.** You can close the tool afterwards; no computer needs to stay running. [Home support, recovery and Undo](NATIVE-HOME.md).

For an unlisted model/software, review **Compatibility results** and choose **Send compatibility report**. A missing getter or failed connection is included without hiding later checks. **Save report** keeps a local copy. Home writes remain blocked until a compatible setup profile is reviewed; you can still use the TV app from Apps.

## 6. Add and open your apps

1. Select **+** using the remote’s centre **OK/Enter** button.
2. Choose an installed app. Its shortcut appears, with another **+** for adding more. You can add up to **nine**.
3. Press **Select** briefly to open a shortcut.
4. To replace it, **hold Select for about one second**, release, then choose another app. **Back** cancels.

![A fresh installation starts with Add app](images/first-run.jpg)

Use **Settings → Apps on Home** to reorder or remove shortcuts. To move one, select its name, use the arrows, then Select to place it. Removing a shortcut leaves the app installed.

**All apps** shows your other apps. **Settings → Background** changes the photo. **Settings → Samsung** opens TV settings and inputs.

## Connection and installation help

| Problem | Try this |
| --- | --- |
| Cannot find the app download | Open the preview release and choose your **CleanHome-Setup** ZIP. Extract it and open **START-HERE.html**. The `.wgt` is included; it is also available separately. |
| TV is missing | Turn it on, check both devices use the same home network, then rescan. You can also enter the TV’s address from its Network Status/IP Settings in the installer. |
| “Developer Mode is off” or TV is not ready | Repeat step 3. **Host PC IP uses the computer’s address.** Selecting the TV in the installer uses the TV’s address. |
| VPN warning or wrong network | Use the home-network address. See the installer’s network help if a VPN affects discovery. |
| No “Install a file…” option | Use a version that supports custom files; see [Apps2Samsung’s guide](https://github.com/Apps2Samsung/Apps2Samsung/wiki). |
| Certificate/signing error | Follow the installer’s certificate help. For an update, use the original signing profile and keep the installed app while fixing it. |
| Missing app or shortcut will not open | **Settings → Application IDs → Refresh installed apps**. For a hidden sideloaded app, that screen also accepts a manually verified app ID for supported services. |
| No daily photo | Choose a bundled photo in **Settings → Background**; these work offline. Check the TV’s internet connection before trying Daily photo again. |

Still stuck? [Report a problem](https://github.com/Dant5/clean-home-tizen/issues) with your TV model, software version, Clean Home version and what happened. Leave out passwords, serial numbers, certificate files and account screens.

## Updates and removal

**To update:** install the new Clean Home file using the same signing profile. This preserves saved shortcuts and settings. Keep a secure backup of that profile. An installer/certificate backup does not contain other apps’ private settings or pairings.

**To remove:** open Samsung **Apps → app settings**, select **Clean Home**, then **Delete**. Menu names vary. Only Clean Home and its saved settings are removed.

If you completed the Home-button/startup step, [use Undo first](NATIVE-HOME.md), and check the physical Home button opens Samsung Home before deleting Clean Home.

Building or signing with Tizen Studio? See the [developer guide](../.github/CONTRIBUTING.md#sign-and-install-with-tizen-studio).
