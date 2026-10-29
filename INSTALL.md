# Install and use Clean Home

This guide installs Clean Home as an ordinary TV app. **No root or jailbreak is required.** Your existing apps stay installed, and your remote’s Home button keeps opening Samsung Home.

The separate Home-button/startup setup used on our test Q60B is not part of these steps. [Read about that option](docs/NATIVE-HOME.md).

**Preview status:** the public download is not available yet. If Releases has no Clean Home `.wgt` file, the preview has not been published. You do not need to download the source code.

## Before you start

Have these ready:

- A Samsung TV. The tested model is the **2022 Q60B with Tizen 6.5**; other models are unconfirmed.
- A Windows, Mac or Linux computer on the same home network as the TV. Wi-Fi or Ethernet is fine if the devices can reach each other.
- A Samsung account for the installer’s certificate setup. A certificate is the file that lets the TV accept an app prepared for it.

The recommended route uses **Apps2Samsung**, a separate open-source installer. It handles app signing and installation. Follow any Samsung sign-in privately in the installer/browser; never post your password or certificate files in an issue.

## 1. Download the two files you need

1. Open [Clean Home Releases](https://github.com/Dant5/clean-home-tizen/releases).
2. Open the preview release and expand **Assets**.
3. Download **`CleanHome-Tizen-1.4.0-unsigned.wgt`**, or the equivalent file for the release you are installing. `.wgt` is the TV app file. “Unsigned” means the installer must prepare it for your TV before installation.
4. Open the [official Apps2Samsung releases](https://github.com/Apps2Samsung/Apps2Samsung/releases). Download the desktop version for your computer, then open it. Use a version that supports installing a file of your own.

Keep the Clean Home file somewhere easy to find, such as Downloads. You do not need the source-code ZIP or a code editor.

<details>
<summary>Optional: check that the download matches the release</summary>

Download `SHA256SUMS` from the same release. Compare the long SHA-256 value for your file with its entry in that text file.

On Windows, open PowerShell in the download folder:

```powershell
Get-FileHash .\CleanHome-Tizen-1.4.0-unsigned.wgt -Algorithm SHA256
```

On macOS:

```sh
shasum -a 256 CleanHome-Tizen-1.4.0-unsigned.wgt
```

On Linux:

```sh
sha256sum CleanHome-Tizen-1.4.0-unsigned.wgt
```

Use your downloaded filename if the version differs. If the values differ, download again before installing.

</details>

## 2. Find your computer’s address

The TV’s setup asks which computer may install apps. It needs **your computer’s local IPv4 address**, not the TV’s address.

| Computer | Where to find it |
| --- | --- |
| Windows | **Settings → Network & internet** → open the connected Wi-Fi/Ethernet connection’s **Properties** → find **IPv4 address**. |
| Mac | **System Settings → Network** → choose the connected Wi-Fi/Ethernet connection → **Details → TCP/IP** → find **IP address**. |
| Linux | Open the connected Wi-Fi/Ethernet connection’s **Details** in your network settings and find its **IPv4 address**. Labels vary by desktop. |

Use the address for the home-network connection, not a VPN, tunnel or virtual adapter. If your settings look different, see [Microsoft’s network help](https://support.microsoft.com/en-us/windows/experience/connectivity-networking/essential-network-settings-and-tasks-in-windows) or [Apple’s TCP/IP settings guide](https://support.apple.com/en-gb/guide/mac-help/mh14129/mac). Read the address; you do not need to change it.

## 3. Enable Developer Mode on the TV

Developer Mode lets the TV accept apps installed from your computer. **It does not root the TV.**

1. Turn the TV on and open **Apps** from Samsung Home.
2. Enter **1 2 3 4 5** with the remote’s number buttons or on-screen number keypad. On some models, open **Apps → App Settings** before entering the numbers.
3. In the Developer Mode window, switch **Developer Mode** to **On**.
4. In **Host PC IP**, enter the **computer address from step 2**.
5. Select **OK** and restart the TV as prompted. A normal restart preserves apps and settings; a Smart Hub or factory reset is not needed.
6. Reopen Apps. Look for the Developer Mode indication.

**Expected result:** Developer Mode is on and lists the computer you are using. If the window does not appear, follow [Samsung’s illustrated TV connection guide](https://developer.samsung.com/smarttv/develop/getting-started/using-sdk/tv-device.html) for your model. Do not enter a service menu or reset the TV.

## 4. Install with Apps2Samsung

1. Open **Apps2Samsung** on the computer from step 2.
2. Select your TV. Check its model; a Samsung soundbar can also appear on the network.
3. Wait for the installer to report that the TV is ready. If it cannot find the TV, use [connection help below](#connection-and-installation-help).
4. Choose **Install a file…**, or your version’s custom `.wgt` option. Select the Clean Home file from Downloads. If there is no file-install option, consult [Apps2Samsung’s guide](https://github.com/Apps2Samsung/Apps2Samsung/wiki) or use a current version that supports it.
5. Follow the installer’s Samsung sign-in and certificate prompts. Use your own account/profile; the installer can reuse an existing compatible one.
6. Continue with installation of **Clean Home**. No root option, other-app reinstall, Smart Hub reset or certificate override is part of this guide.
7. Wait for success, then open **Clean Home** from the TV’s **Apps** screen if it has not opened already.

**Expected result:** a photograph, clock and one **+** tile on a fresh installation. If updating an existing Clean Home installation, your saved apps stay in place instead.

The file-install label is taken from Apps2Samsung’s current desktop source; older versions and translations can look different. Its own [project guide](https://github.com/Apps2Samsung/Apps2Samsung) describes custom-file installation and certificate handling. The latest installer’s complete workflow has not been independently tested by this project on every supported computer.

## 5. Choose your apps

1. Select **+** with the centre **OK/Enter** button on the remote.
2. Choose an app already installed on the TV. It is added to the app bar without launching or reinstalling it.
3. Select the next **+** to add another app. You can add up to **nine**.
4. Press Select briefly on an app tile to open it.
5. To replace a tile, **hold Select for about one second**, release it, then choose the replacement. Press **Back** to cancel.

![A fresh installation starts with Add app](docs/images/first-run.jpg)

For reordering or removal, open **Settings → Apps on Home**. Choose an app name to move it, use the arrows, then Select to place it; Back cancels a move. **Remove from Home** removes only the shortcut, keeping the app installed. The editor keeps at least one shortcut once apps have been added.

**All apps** opens the installed-app list. **Settings → Background** changes the photo or turns daily photos off. **Settings → Samsung** provides TV settings and input controls. With this standard installation, pressing the remote’s **Home** button opens Samsung Home as usual; reopen Clean Home from Apps when you want it.

The new add/replace flow is browser-tested. Physical-remote confirmation is still pending for this preview; report unexpected behaviour with your model and software version.

## Connection and installation help

| What you see | What to do |
| --- | --- |
| No `.wgt` in Clean Home Releases | The public download is not published yet. A source-code ZIP is not the installable TV app. |
| TV is missing | Check that the TV is on and both devices are on the same home network. Rescan in Apps2Samsung. If needed, find the TV’s address in its Network Status/IP Settings and use the installer’s manual-address option. |
| “Developer Mode is off” or TV is not ready | Recheck step 3. **Host PC IP is the computer’s address.** The TV address is used when selecting/adding the TV in the installer. They are two different addresses. |
| Wrong network address or a VPN warning | Use the computer’s home-network address. A VPN/virtual adapter can affect discovery; consult the installer’s network help before changing connections. |
| Certificate/signing error | Follow the installer’s certificate help. For an update, reuse the original author profile. Keep the installed app while resolving the issue. |
| No apps in the chooser, or one is missing | Open **Settings → Application IDs → Refresh installed apps** in Clean Home. Some unusual sideloaded apps may be hidden; the known-service controls on that screen accept a manually verified app ID. |
| A shortcut will not open its app | Refresh installed apps and check the selected build. App identifiers can differ between TVs and between Legacy/current app versions. |
| No daily photo | Pick a bundled photo under **Settings → Background**. These work offline. Check the TV’s internet connection before trying Daily photo again. |
| Home opens Samsung Home | That is expected after this installation. The separate [Home/startup setup](docs/NATIVE-HOME.md) is not included. |

If you still need help, [report a problem](https://github.com/Dant5/clean-home-tizen/issues) with the TV model, software version, Clean Home version, what you pressed and what happened. A photo of just the problem helps. Leave passwords, account screens, serial numbers and certificate files out of the report.

## Updating without losing settings

Install the new Clean Home file with the **same signing profile** used before. Keep that profile backed up securely using your installer’s backup feature where available. Reusing it lets the TV recognise an update to the same app.

Saved Clean Home favourites, order, appearance and manually entered app IDs are preserved by a normal same-identity update. A signing error is a reason to fix the profile, not to uninstall your other apps or reset Smart Hub.

Backing up the installer or its certificates does **not** back up other apps’ private accounts, settings or Moonlight pairings. Clean Home does not extract that private data; it leaves those apps in place.

## Removal and recovery

For the standard installation in this guide:

1. Open Samsung’s **Apps** screen and its app settings.
2. Select **Clean Home**, then **Delete**. Menu names vary by TV.
3. Samsung Home and your other apps stay installed. Clean Home’s own saved shortcuts/settings are removed with it.

**If you separately changed the Home-button or power-on setup, restore that setup before deleting Clean Home.** Use your own saved original Home and Last App settings and verify that the physical Home button opens Samsung Home. Removing an app does not undo those separate TV changes. [Advanced recovery information](docs/NATIVE-HOME.md).

<details>
<summary>Advanced: Tizen Studio, signing and app identity</summary>

This section is for developers; the Apps2Samsung route above is intended for ordinary installation.

The package is `D5Q60BHome`; application ID is `D5Q60BHome.CleanHome`. If that identity already belongs to something unexpected, stop rather than overwrite it. Do not copy a different developer’s signing identity.

With Tizen Studio, install Samsung TV Extensions and Samsung Certificate Extension. Create your own Samsung TV author/distributor profile in Certificate Manager, covering your TV’s DUID. See [Samsung certificate creation](https://developer.samsung.com/smarttv/develop/getting-started/setting-up-sdk/creating-certificates.html).

After building, use your profile to sign the widget, for example:

```sh
tizen package -t wgt -s YOUR_PROFILE -o dist/sdk-signed -- dist/CleanHome-Q60B-unsigned.wgt
```

Install the signed result with the SDK’s normal device tools. The optional standalone signer accepts `scripts/package.py --cert-dir /outside/repository/certs` with `author.p12`, `distributor.p12` and `password.txt`. Keep credentials outside the repository with owner-only permissions. Public release builds do not take certificates or a personal app profile. [Build instructions](CONTRIBUTING.md).

</details>
