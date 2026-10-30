# Development and contributions

The front-page installation guide is for people using the ready-made download. This page is for developers building or testing the source. Keep private certificates, diagnostic logs and TV recovery state outside Git.

## Set up a local checkout

Requirements: Node 22+ and Python 3.10+ with venv/pip support. These commands use Linux/macOS paths. On Debian/Ubuntu, install `python3-venv` if the venv command reports missing ensurepip.

```sh
npm ci
python3 -m venv .local/venv
.local/venv/bin/python -m pip install -r scripts/requirements-build.txt
npx playwright install chromium
npm run dev:public
```

Open the localhost address printed by the preview. Arrows, Enter and Escape correspond to the remote. A desktop browser cannot discover a television’s apps; installed-app choices require the TV, while tests supply a mock inventory. The public preview uses Manrope, Geist and Newsreader; no proprietary font files are needed.

On headless Linux, `npx playwright install --with-deps chromium` installs the browser/runtime dependencies on that machine. Browser checks mock only the Tizen boundary and external pictures; they must never contact a real TV.

## Build and validate

`npm run package` creates `dist/CleanHome-Q60B-unsigned.wgt`. It includes public fonts and notices without a device profile or signing keys. Consumer TVs require local signing before installation. See [signing below](#sign-and-install-with-tizen-studio) for developer installation.

```sh
npm test
npm run check:performance
npm run package
npm run check:package
npm run check:public
```

`npm test` covers ES5/resource checks, device adapter, original UI, Q60B integration, photo recovery, early input, first-run selection and background comparisons. Python tests cover packaging/signing and supporting parsers using fake certificates/devices. The built-widget check examines the actual unsigned download. CI is configured for a current browser and Chromium 85. See the [validation record](../docs/TEST-RESULTS.md) for actual local results and any hosted-run limitation. Neither proves behaviour on an untested TV.

For a locally installed historical engine, set `CLEANHOME_CHROMIUM=/path/to/chrome`. `scripts/install-test-browser.py` downloads/checks the pinned Linux test snapshot used in CI. Use it for isolated local test pages, not general browsing. Its exact version is reported in test output.

The background shading cache is generated with Chromium 85:

```sh
CLEANHOME_CHROMIUM=/path/to/chrome85 npm run build:backgrounds
```

Regenerate after changing its CSS, wallpaper catalogue or adaptive-ink inputs; a Python check detects stale source hashes. Generated images contain only transparent CSS shading, without photographs. Do not replace visual-regression checks with screenshots of private account screens.

Keep the original appearance and licences. Test both a fresh empty configuration and an upgrade with saved favourites. Do not hard-code personal app IDs, addresses, DUIDs or certificate profiles. A public release must use generic discovery and the unsigned public-font package. Treat native Home/startup as separate, firmware-specific work with per-device originals and a verified inverse path; never relax the guards to get a test to pass.

Bug reports should include a reproducible sequence, expected/actual result, model, firmware, Tizen/app version and installation method. Use the issue forms and label whether the result was visually observed, reported by an API or only simulated.

The in-app **Share TV report** sheet prepares a GitHub draft locally. `npm run check:reports` tests its allowlisted fields, real remote events, failure/cancellation and independent QR decoding of rendered screenshots at 1080p/720p. `npm run check:package` repeats the UI checks against the actual widget. The QR encoder loads only when requested; never add automatic uploads or raw logs. [Report fields and maintaining the compatibility chart](../docs/TV-REPORTS.md).

## Sign and install with Tizen Studio

The package is `D5Q60BHome`; application ID is `D5Q60BHome.CleanHome`. Check that neither belongs to another installed application before installing.

Install Samsung TV Extensions and Samsung Certificate Extension in Tizen Studio. Create your own author/distributor profile in Certificate Manager, covering the TV’s DUID. See [Samsung’s certificate guide](https://developer.samsung.com/smarttv/develop/getting-started/setting-up-sdk/creating-certificates.html). Keep the same author profile for updates; never use another developer’s identity.

Sign the built widget with your profile:

```sh
tizen package -t wgt -s YOUR_PROFILE -o dist/sdk-signed -- dist/CleanHome-Q60B-unsigned.wgt
```

Install the signed result with the SDK device tools. The standalone signer also accepts `scripts/package.py --cert-dir /outside/repository/certs` containing `author.p12`, `distributor.p12` and `password.txt`. Keep credentials outside Git with owner-only permissions. Public release builds accept no certificates or personal profiles.

## Privacy checks

Run `npm run check:public` and `sh scripts/check-secrets.sh` before pushing or preparing a release. The guards reject device/network addresses, local user paths, identifiers and signing material; image checks detect location, owner and camera metadata. Test fixtures use loopback or reserved documentation addresses. These checks supplement manual review and cannot detect every kind of private content.

Keep Web Inspector sessions on a trusted network and close them after testing.

## TV-generation compatibility

`python3 scripts/install-test-browser.py --engine 63` installs an official, checksum-pinned Chromium snapshot in `.local/chromium63`. Engines 69, 76, 85, 94, 108, 120 and 130 are also pinned. Set `CLEANHOME_CHROMIUM` to its executable and run `npm run package && npm run check:compatibility`. Historical binaries are for these local pages only. Ubuntu test dependencies include libgtk-3-0, libxss1, libgconf-2-4, libxshmfence1, libgbm1 and libasound2.

The compatibility runner reuses the packaged-widget preview and onboarding fixture. It uses basic page DevTools commands because old engines lack Playwright's browser-context download methods. It checks real DOM remote events, saved choices and geometry, while mocking the Tizen boundary and blocking remote network requests. Browser results do not establish Samsung certificate acceptance or hardware/API behaviour on an untested TV.

`app/compatibility.css` contains margin equivalents for the original flex gaps. Regenerate it with `python3 scripts/build-compatibility-css.py` after changing gap rules in `style.css`. The one-time feature probe enables it only where actual flex gap is missing. Modern engines also test the fallback against their native geometry.
