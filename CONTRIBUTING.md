# Development and contributions

The front-page installation guide is for people using the ready-made download. This page is for developers building or testing the source. Keep private certificates, diagnostic logs and TV recovery state outside Git.

## Set up a local checkout

Requirements: Node 22+ and Python 3.10+ with venv/pip support. These commands use Linux/macOS paths. On Debian/Ubuntu, install `python3-venv` if the venv command reports missing ensurepip.

```sh
npm ci
python3 -m venv .local/venv
.local/venv/bin/python -m pip install -r requirements-build.txt
npx playwright install chromium
npm run dev:public
```

Open the localhost address printed by the preview. Arrows, Enter and Escape correspond to the remote. A desktop browser cannot discover a television’s apps; installed-app choices require the TV, while tests supply a mock inventory. The public preview uses Manrope, Geist and Newsreader; no proprietary font files are needed.

On headless Linux, `npx playwright install --with-deps chromium` installs the browser/runtime dependencies on that machine. Browser checks mock only the Tizen boundary and external pictures; they must never contact a real TV.

## Build and validate

`npm run package` creates `dist/CleanHome-Q60B-unsigned.wgt`. It includes public fonts and notices without a device profile or signing keys. Consumer TVs require local signing before installation. See the advanced section of [INSTALL.md](INSTALL.md) for the supported signing routes.

```sh
npm test
npm run check:performance
npm run package
npm run check:package
npm run check:public
```

`npm test` covers ES5/resource checks, device adapter, original UI, Q60B integration, photo recovery, early input, first-run selection and background comparisons. Python tests cover packaging/signing and supporting parsers using fake certificates/devices. The built-widget check examines the actual unsigned download. CI is configured for a current browser and Chromium 85. See the [validation record](docs/TEST-RESULTS.md) for actual local results and any hosted-run limitation. Neither proves behaviour on an untested TV.

For a locally installed historical engine, set `CLEANHOME_CHROMIUM=/path/to/chrome`. `scripts/install-test-browser.py` downloads/checks the pinned Linux test snapshot used in CI. Use it for isolated local test pages, not general browsing. Its exact version is reported in test output.

The background shading cache is generated with Chromium 85:

```sh
CLEANHOME_CHROMIUM=/path/to/chrome85 npm run build:backgrounds
```

Regenerate after changing its CSS, wallpaper catalogue or adaptive-ink inputs; a Python check detects stale source hashes. Generated images contain only transparent CSS shading, without photographs. Do not replace visual-regression checks with screenshots of private account screens.

Keep the original appearance and licences. Test both a fresh empty configuration and an upgrade with saved favourites. Do not hard-code personal app IDs, addresses, DUIDs or certificate profiles. A public release must use generic discovery and the unsigned public-font package. Treat native Home/startup as separate, firmware-specific work with per-device originals and a verified inverse path; never relax the guards to get a test to pass.

Bug reports should include a reproducible sequence, expected/actual result, model, firmware, Tizen/app version and installation method. Use the issue forms and label whether the result was visually observed, reported by an API or only simulated. No support-time guarantee is offered.
