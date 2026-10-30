# Share your TV results

Tried Clean Home on another Samsung TV? Reports of success are as useful as bug reports.

1. Open **Settings → Samsung → Share TV report** in Clean Home 1.4.2 or newer.
2. Review the details shown on screen.
3. Choose **Send: works** or **Send: problem**. No phone, QR code or account is required.
4. Wait for **Thank you** and a receipt. That confirms the receiver accepted your report.

The report fills in the TV model, firmware, Tizen version, browser generation, app version, app surface size and basic loading checks. Unavailable details say **Not reported**; you can add your exact model from **TV Settings → Support → About This TV**. Do not include the serial number.

Nothing is sent until you choose **Send**. The details go to the project's [feedback receiver](https://clean-home-feedback.perkymule6.chatgpt.site), in a private maintainer database. They are not automatically posted to GitHub, sent to Samsung or delivered to a running AI chat. Reviewed compatibility findings may be added to the public chart. There is no background retry or offline queue. Double presses are ignored while sending; successful sends have a one-minute cooldown.

If delivery cannot be confirmed, a report may already have arrived. Try again only if you choose. Back closes the sheet and cancels a pending request; it cannot retract a report already received. For a detailed explanation, [open a GitHub issue](https://github.com/Dant5/clean-home-tizen/issues/new?template=tv-report.yml) and include the receipt. This is optional.

No installed-app list, app IDs, accounts, pairing data, network addresses, serial numbers, DUIDs, signing material, screenshots or raw logs are collected for sharing. Error counters and the last TV error category/code are included, without error messages or URLs. The hosting provider sees normal web-request information, including your internet address; the database does not store it. Reports older than 90 days are pruned on incoming submissions. [Receiver source](../tools/report-service/README.md).

**Use phone** remains available if direct sending fails. Choose an outcome, scan the QR code, sign in to GitHub, review the draft and submit. Scanning sends the prefilled details to GitHub; submitting makes them public. This fallback requires a phone and GitHub account.

If the app will not open, the QR code fails, or you are using an older Clean Home version, [open a TV report manually](https://github.com/Dant5/clean-home-tizen/issues/new?template=tv-report.yml). A cropped photo is optional; leave account screens out.

## What helps us

Say which things you actually tried: installation, arrows/Select/Back, adding and opening apps, photo loading, HDMI, Samsung Home and TV settings. For a problem, describe what you pressed and what appeared. If possible, say whether reopening Clean Home helped. Do not reset Smart Hub or reinstall your favourite apps to investigate a launcher problem.

## Maintaining the chart

The [compatibility chart](COMPATIBILITY.md) separates an intended OS target, a passing browser check and real-TV evidence. An API being present, a launch callback or a submitted “works” report does not automatically verify a TV.

Review each community report for the exact model, firmware, Clean Home version, installation method, visually observed checks and any separate native Home setup. Ask for missing details in the issue rather than promoting an OS from an incomplete report. Add accepted evidence, its issue link and its limited tested scope to `docs/compatibility.json`; keep community-reported results separate from the development reference. Regenerate with `python3 scripts/build-compatibility-chart.py`. Never claim that one model verifies every TV running that Tizen version. Home/startup compatibility remains a separate firmware-specific question.

The model/firmware getters use Samsung's public [ProductInfo API](https://developer.samsung.com/smarttv/develop/api-references/samsung-product-api-references/productinfo-api.html). OS version comes from [SystemInfo](https://developer.samsung.com/smarttv/develop/api-references/tizen-web-device-api-references/systeminfo-api.html), with a parsed Tizen user-agent version as fallback; it is never guessed from the browser generation. Report links use [GitHub's documented issue query fields](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-an-issue#creating-an-issue-from-a-url-query).
