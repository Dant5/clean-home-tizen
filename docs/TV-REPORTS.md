# Share your TV results

Tried Clean Home on another Samsung TV? Reports of success are as useful as bug reports.

1. Open **Settings → Samsung → Share TV report** in Clean Home 1.4.2 or newer.
2. Choose **Works on my TV** or **Report a problem**.
3. Scan the QR code with your phone's camera.
4. Sign in to GitHub, review the details and add a sentence about what you tried. Choose **Submit new issue**.

The report fills in the TV model, firmware, Tizen version, browser generation, app version, app surface size and basic loading checks. Unavailable details say **Not reported**; you can add your exact model from **TV Settings → Support → About This TV**. Do not include the serial number.

The TV prepares the code locally. It does not upload a report, open a browser or interrupt your apps. Scanning opens a GitHub draft on your phone; submitting makes it public. It needs a GitHub account. Reports go to this project's [GitHub issues](https://github.com/Dant5/clean-home-tizen/issues), where maintainers can review them; they are not sent directly to an AI or Samsung.

No installed-app list, app IDs, accounts, pairing data, network addresses, serial numbers, DUIDs, signing material, screenshots or raw logs are collected for sharing. Error counters and the last TV error category/code are included, without error messages or URLs. GitHub receives the report details when you open the scanned link; review the on-TV summary first.

If the app will not open, the QR code fails, or you are using an older Clean Home version, [open a TV report manually](https://github.com/Dant5/clean-home-tizen/issues/new?template=tv-report.yml). A cropped photo is optional; leave account screens out.

## What helps us

Say which things you actually tried: installation, arrows/Select/Back, adding and opening apps, photo loading, HDMI, Samsung Home and TV settings. For a problem, describe what you pressed and what appeared. If possible, say whether reopening Clean Home helped. Do not reset Smart Hub or reinstall your favourite apps to investigate a launcher problem.

## Maintaining the chart

The [compatibility chart](COMPATIBILITY.md) separates an intended OS target, a passing browser check and real-TV evidence. An API being present, a launch callback or a submitted “works” report does not automatically verify a TV.

Review each community report for the exact model, firmware, Clean Home version, installation method, visually observed checks and any separate native Home setup. Ask for missing details in the issue rather than promoting an OS from an incomplete report. Add accepted evidence, its issue link and its limited tested scope to `docs/compatibility.json`; keep community-reported results separate from the development reference. Regenerate with `python3 scripts/build-compatibility-chart.py`. Never claim that one model verifies every TV running that Tizen version. Home/startup compatibility remains a separate firmware-specific question.

The model/firmware getters use Samsung's public [ProductInfo API](https://developer.samsung.com/smarttv/develop/api-references/samsung-product-api-references/productinfo-api.html). OS version comes from [SystemInfo](https://developer.samsung.com/smarttv/develop/api-references/tizen-web-device-api-references/systeminfo-api.html), with a parsed Tizen user-agent version as fallback; it is never guessed from the browser generation. Report links use [GitHub's documented issue query fields](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query).
