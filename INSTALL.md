# Install, update and remove

The download installs as an ordinary Samsung TV web application. It does not change native Home/startup, firmware, protected packages, picture/sound settings or other applications.

## Apps2Samsung route

1. Use a computer on the TV’s local network. In the TV’s **Apps** screen, enter **1 2 3 4 5** to open Developer Mode on the reference 2022 model. Turn it on and enter the **installer computer’s LAN IPv4 address** as Host PC IP. This is different from the TV address. Restart normally if prompted. Other models may use different controls; follow [Samsung’s device guide](https://developer.samsung.com/smarttv/develop/getting-started/using-sdk/tv-device.html).
2. Obtain Apps2Samsung from [its official project](https://github.com/Apps2Samsung/Apps2Samsung). Select the TV and verify its model. Do not confuse a soundbar with the TV. If readiness fails, check the local address, Host PC IP and Developer Mode before changing network settings.
3. Choose its **custom `.wgt`** option and select this release’s unsigned widget. Let the installer create/reuse your own Samsung certificate profile. Any Samsung login happens privately in the installer/browser; this project does not need your password or certificate files.
4. Install only Clean Home, then open it from Apps. The package is `D5Q60BHome`, application `D5Q60BHome.CleanHome`. If that identity already belongs to something unexpected, stop rather than overwrite it.
5. Select **+** and choose an installed application. Selection adds the app to Home; it does not launch or reinstall it. Another + remains until the nine-app limit. Hold Select on an existing tile to replace it, or use Settings → Apps on Home to reorder/remove.

Apps2Samsung supports custom widgets and local certificate handling; its exact screen labels vary by version. No root option, forced certificate override, Smart Hub reset or favourite-app reinstall is required. We have not tested every installer/platform combination. Keep the installation result separate from whether an application visibly opened.

## Tizen Studio alternative

Install Samsung TV Extensions and Samsung Certificate Extension, then create your own Samsung TV author/distributor profile in Certificate Manager. The distributor certificate must cover your TV’s DUID. See [Samsung certificate creation](https://developer.samsung.com/smarttv/develop/getting-started/setting-up-sdk/creating-certificates.html).

After building the unsigned widget, use your profile with the SDK’s packager, for example:

```sh
tizen package -t wgt -s YOUR_PROFILE -o dist/sdk-signed -- dist/CleanHome-Q60B-unsigned.wgt
```

Install the resulting signed widget using the SDK’s normal device tools. Never use another developer’s author identity. `scripts/package.py --cert-dir /outside/repository/certs` is an optional standalone signer expecting `author.p12`, `distributor.p12` and `password.txt`; credentials stay outside Git, with owner-only permissions. The release builder never takes a certificate or app-binding profile.

## Updating without losing settings

Keep the same application identity and author certificate. Save a copy of the previous widget and securely export/back up the installer’s signing profile where supported. An author-certificate mismatch is a reason to resolve signing, **not** to uninstall other apps or reset Smart Hub.

Existing Clean Home saved favourites/order, appearance and manual bindings remain local and are preserved by an in-place same-identity update. The first-run + dock applies to a fresh configuration. Clean Home cannot migrate another application’s private storage simply because it has a similar name.

Installer/certificate backups do not contain Nuvio, Moonlight, YouTube or Spotify private accounts, settings or pairings. Tizen isolates those applications. This launcher launches the existing installations; it provides no private-data extraction or full TV backup.

## Removal and recovery

For an ordinary installation with **no native Home changes**, open Samsung Apps → app settings, select Clean Home and Delete. This removes only the launcher and its local preferences. Keep your signing profile if you may reinstall later.

**If you separately changed native Home/startup, restore both your own original Home snapshot and Last App setting, verify the physical Home button opens Samsung’s interface, and only then uninstall.** The widget cannot automatically undo a configuration applied outside it. Do not copy another TV’s original values. Keep the launcher installed while a restore is unresolved. See [native Home scope](docs/NATIVE-HOME.md).

Do not use a service menu, factory reset, package debloat or firmware change to troubleshoot this app. If ordinary device menus or developer access are unavailable, follow Samsung’s support/recovery instructions for the exact model.

## Quick troubleshooting

| Symptom | First step |
| --- | --- |
| Installer cannot see the TV | Confirm the selected device is the TV, Developer Mode is on, and Host PC IP is the installer computer's local address. |
| Certificate or update rejected | Reuse the original author profile and a distributor certificate for this TV. Keep the previous installation while resolving signing. |
| An installed app is missing | Open Clean Home Settings → Application IDs → Refresh installed apps. Unusual sideloaded builds may need a manually verified ID; the known-service binding controls are on that screen. |
| A tile cannot open its app | Refresh discovery and verify the selected build/ID. App IDs can differ between models and between Legacy/current builds. |
| Daily picture is unavailable | A bundled photo should remain available. Choose a bundled wallpaper in Settings → Background; check network availability before re-enabling Daily photo. |
| Physical Home still opens Samsung Home | This is expected after an ordinary widget installation. Native Home/startup is a separate firmware-specific procedure, not part of this download. |

If these steps do not resolve the issue, report the model, firmware, launcher version and shortest reproduction. A cropped screen photo helps; keep accounts and device identifiers out of it.
