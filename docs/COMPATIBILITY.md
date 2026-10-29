# TV compatibility

| TV | Status |
| --- | --- |
| **2022 Samsung Q60B, Tizen 6.5** | Reference model used for development. |
| Other Samsung Tizen TVs | Unconfirmed. Please [share your results](https://github.com/Dant5/clean-home-tizen/issues/new?template=compatibility.yml). |
| TVs from other brands | Not supported. |

The reference model is QA55Q60BAWXXY, running T-NKLBUABC-1720.7. Matching Tizen versions alone does not guarantee compatibility.

## What to expect

- The layout scales to your screen; a 55-inch or 4K TV is not required.
- The dock holds up to nine apps. Some hidden sideloaded apps may need a manually verified ID in **Settings → Application IDs**.
- App IDs can differ between TVs and between builds of the same app. Clean Home discovers yours rather than using another TV’s list.
- Developer Mode and certificate availability depend on your TV and region. Use the same signing profile for updates.
- The standard download does not change the Home button or power-on behaviour. The separate [native setup](NATIVE-HOME.md) is specific to the reference TV’s software.

The preview has not been verified on every model or with every input/remote feature. Detailed hardware coverage and outstanding checks are in the [developer test record](TEST-RESULTS.md).

## For developers

The runtime uses ES5-compatible JavaScript and targets Chromium 85. The original 1920×1080 stage scales proportionally to the viewport. A 4K panel can use a 1080p application surface; see [Samsung’s resolution guide](https://developer.samsung.com/smarttv/develop/guides/fundamentals/managing-screen-resolution.html). Browser layout checks do not establish native API compatibility on another TV.
