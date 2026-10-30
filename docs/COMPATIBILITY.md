# TV compatibility

This build requires **Tizen 5.0 or newer**.

![Clean Home compatibility by Tizen version](images/compatibility.svg)

**Preview target** means the app is designed for that version. **Browser check** means it passed in the corresponding desktop browser engine with simulated TV APIs. **Actual TV** identifies limited real hardware evidence; it does not verify every model running that OS. Model years are a guide because some TVs can receive OS upgrades.

| TV | Status |
| --- | --- |
| **2022 Samsung Q60B, Tizen 6.5** | Reference model used for development. |
| Tizen 5.0, 5.5, 6.0, 7.0, 8.0, 9.0 and 10.0 | Preview targets; please [share your results](https://github.com/Dant5/clean-home-tizen/issues/new?template=compatibility.yml). |
| Tizen 4.0 and earlier | Outside this build’s compatibility target. |
| TVs from other brands | Not supported. |

The reference model is QA55Q60BAWXXY, running T-NKLBUABC-1720.7. Matching Tizen versions alone does not guarantee compatibility.

The reference TV runs Clean Home **1.3.9**. The newer public app chooser and TV-report flow have browser coverage; that exact public build has not been installed on the reference TV. No additional community models are confirmed yet.

**Help fill in the chart:** in Clean Home 1.4.2+, open **Settings → Samsung → Share TV report**, choose Works or Report a problem, and scan the code. [Share your TV results](TV-REPORTS.md). Older builds or installation failures can use the same manual report form.

## What to expect

- The layout scales to your screen; a 55-inch or 4K TV is not required.
- The dock holds up to nine apps. Some hidden sideloaded apps may need a manually verified ID in **Settings → Application IDs**.
- App IDs can differ between TVs and between builds of the same app. Clean Home discovers yours rather than using another TV’s list.
- Developer Mode and certificate availability depend on your TV and region. Use the same signing profile for updates.
- The standard download does not change the Home button or power-on behaviour. The separate [native setup](NATIVE-HOME.md) is specific to the reference TV’s software.

The preview has not been verified on every model or with every input/remote feature. Detailed hardware coverage and outstanding checks are in the [developer test record](TEST-RESULTS.md).

## For developers

The runtime uses ES5-compatible JavaScript and targets Chromium 63 and newer. The original 1920×1080 stage scales proportionally to the viewport. A 4K panel can use a 1080p application surface; see [Samsung’s resolution guide](https://developer.samsung.com/smarttv/develop/guides/fundamentals/managing-screen-resolution.html). Browser layout checks do not establish native API compatibility on another TV.

Samsung maps Tizen 5.0 / 5.5 / 6.0 / 6.5 / 7.0 / 8.0 / 9.0 / 10.0 to Chromium 63 / 69 / 76 / 85 / 94 / 108 / 120 / 130 respectively. See [Samsung’s engine specifications](https://developer.samsung.com/smarttv/develop/specifications/web-engine-specifications.html). The APIs used for application discovery and input switching predate the 5.0 minimum; see [Application](https://developer.samsung.com/smarttv/develop/api-references/tizen-web-device-api-references/application-api.html) and [TVWindow](https://developer.samsung.com/smarttv/develop/api-references/tizen-web-device-api-references/tvwindow-api.html).
