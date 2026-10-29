# Compatibility and limits

| Area | Evidence |
| --- | --- |
| Reference TV | Samsung **QA55Q60BAWXXY**, 2022 Q60B 55-inch |
| Reference firmware | **T-NKLBUABC-1720.7**, Tizen **6.5**, TV Chromium **85.0.4183.93** |
| Launcher core through 1.3.9 | Owner-installed, four app launches/Home returns, daily picture and saved preferences verified |
| Wake responsiveness after shading cache | Owner reports immediate early arrows **respond promptly** after approximately 30 seconds in standby; no millisecond guarantee |
| New 1.4.0 first-run picker / long press | Browser integration checks in Chromium 85 and current Chromium; physical-remote confirmation still pending |
| Native Home/startup | Separately configured and restored/tested on the reference Q60B; not enabled by the public widget |
| Other Samsung models / firmware | Not verified by this project; Tizen 6.5 alone does not prove compatibility |
| HDMI switching | Public TVWindow/SystemInfo adapter and mocked integration tests; full physical HDMI/eARC/audio/CEC behaviour not comprehensively verified |
| Developer text entry | Manual-ID entry is available; physical on-screen keyboard behaviour remains a separate device check |
| Mains cold boot / long soak | No new mains cold-boot or multi-day guarantee for this public preview |

The web runtime stays ES5-compatible and avoids Chromium features unavailable in version 85. Browser CPU throttling is a regression screen, not an emulation of the TV’s GPU or decoder. API visibility is not proof that a frame was visible or an early key responded.

The dock holds up to nine apps. The list uses Samsung’s installed-app catalogue and consumer-app filtering, which can omit unusual hidden packages. Known services have manual-ID controls in Settings → Application IDs. Do not assume another owner’s app IDs or a similar package name. Modern Nuvio and Nuvio Legacy are distinct builds; ordinary catalogue entries can be chosen independently.

Developer Mode, certificate availability and installer support vary by TV/region. Keep the same author certificate when updating. Firmware changes may change undocumented native behaviour. This release does not disable Samsung updates, remove system packages, remap native keys or promise access to isolated application data.

Please submit a compatibility report with the exact model, firmware, Tizen version, app version, installation method and what you actually observed. Exclude addresses, serials, DUIDs and private screenshots.

## Screen size and resolution

Physical panel size does not select a separate layout. The original 1920×1080 stage fits the available viewport and preserves 16:9 proportions. Samsung’s [screen-resolution guidance](https://developer.samsung.com/smarttv/develop/guides/fundamentals/managing-screen-resolution.html) recommends this design size and describes platform scaling; its [current specification table](https://developer.samsung.com/smarttv/develop/specifications/general-specifications.html) lists 1920×1080 application resolution across TV models. A 4K panel can therefore use a 1080p app surface. Browser 720p/4K results establish layout fit, not installation or native API compatibility on an untested television.
