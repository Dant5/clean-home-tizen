# Preview validation

Release candidate: **1.4.0**, prepared 29 October 2026. This is a clean source export with a new first-run dock, not a deployment to another model. The owner's installed 1.3.9 remains separate.

## Local results

| Check | Current Chromium 156.0.8078.4 | Chromium 85.0.4182.0 |
| --- | --- | --- |
| Existing UI and preference regressions | 352 passed | 352 passed |
| Q60B adapter/UI integration | 42 passed | 42 passed |
| Bing selection and recovery | 13 passed | 13 passed |
| Failure injection and resource lifecycle | 15 scenarios passed | 15 scenarios passed |
| Fresh setup, add, replace, duplicate/capacity, save failure and upgrade | 26 passed | 26 passed |
| Early keyboard input with catalogue pending | 48 events passed | 48 events passed |
| Original CSS versus cached background shading | 30 variants passed | 30 variants passed |
| Viewport fit and navigation, seven resolutions/aspect ratios | 35 passed | 35 passed |
| Actual generic unsigned widget | 8 passed | 8 passed |
| Performance/resource regression checks | 43 passed | 43 passed |

Device adapter: **21** tests passed. Python packaging, signer, transport/parser and release-boundary tests: **48** passed. Native helper fake-platform policy: **40** checks passed; helper targets build without errors. Their legacy target-framework warnings are expected because they match the existing TV runtime; no runtime is installed on a television.

The historical test engine is a checksum-pinned official Chromium snapshot. It approximates the TV's Chromium generation, not its Samsung patches, GPU, decoder or hardware. Browser checks use mock device/network boundaries and do not contact a TV. The viewport suite covers 1280×720, 1366×768, 1920×1080, 2560×1440, 3840×2160, 2560×1080 and 1024×768. The original 16:9 stage is scaled/letterboxed without clipping or multiple visible focus targets.

One initial rapid-wallpaper stress run exposed a test race: preference/state readiness can precede the displayed image's asynchronous load event. The cycle check now waits for both settled state and the actual matching decoded display image, with a bounded timeout; it still checks resource growth and persistence. A focused rerun passed. No image check was removed.

## Hardware evidence and limits

The launcher core through 1.3.9 was installed and visually used on the reference Q60B. After the original shading was cached, the owner reported that immediate arrows after standby/wake **respond promptly**. Earlier developer traces measured 81–88% less aggregate raster work, not an equivalent percentage improvement in total startup time or a guaranteed input bound.

The new 1.4.0 + tile and short/long Select behaviour are browser-tested. A physical-remote first-run/hold test remains pending. Other TVs, their firmware, complete HDMI/eARC/CEC behaviour, on-screen keyboard variants, mains cold starts and multi-day operation are unverified. See [compatibility](COMPATIBILITY.md).

Documentation images are offline browser renders with a mock app inventory and fixed clock; they are not photographs of another owner's television. Release assets are unsigned and contain public fonts. Signing/installing requires each owner's own Samsung profile. Hosted CI status and final artifact checksums are recorded separately by the repository Actions run and release manifest.

## Hosted CI status

Hosted validation has not completed for this preview. The local results above are complete; no successful hosted run is claimed. Keep the preview draft unpublished until the required hosted and physical-remote checks are complete. Private maintainer diagnostics are kept outside the repository.

## Publication privacy checks

The source/release guards also reject accidental network addresses, local user paths, hardware identifiers and signing material. Image metadata is checked for location and device/owner identifiers. These checks use synthetic data; they do not connect to a TV. They supplement manual asset review and full-history secret scanning. Original code, image and font credits are retained.
