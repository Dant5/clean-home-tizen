# Dock icon sources (v1.2.3)

All dock marks are single-ink white, drawn with CSS `mask-image` in `currentColor`, and optically sized with
`app/assets/icons/metrics.js` (240px ink-box metrics, the same method as CleanFrame). Every source is >= 2x the
on-screen size (dock marks render at about 72px).

| App | File | Source |
|---|---|---|
| HDMI | `mono/hdmi.png` (256px) | Generated from the bundled 512px TV-outline tile (`scripts/make-mono-marks.py`) |
| YouTube | `youtube.svg` | CleanFrame / Simple Icons (CC0), vector |
| Netflix | `netflix.svg` | CleanFrame / Simple Icons, vector |
| ZEE5 | `mono/zee5.png` (256px) | Keyed from the bundled 512px official ZEE5 tile |
| Prime Video | `primevideo.svg` | CleanFrame custom brand icon, vector |
| JioHotstar | `mono/hotstar.png` (512px) | Star geometry (ray tips + hub) from the official 2025 logo, Wikimedia Commons `File:JioHotstar 2025.png` (3027x797), re-rendered at 2048px and downsampled |
| Sony LIV | `sonyliv.svg` | Vector: Sony wordmark path from Simple Icons (CC0) + clean redraw of the liv mark (ref. Commons `File:SonyLIV 2020.png`, 500px) |
| Internet | `mono/browser.png` (512px) | Official Samsung Internet 2025 logo, Commons `File:Samsung Internet logo 2025.svg`, rendered at 1024px; planet and orbit keyed with a separation line |
| SmartThings (added apps) | `smartthings.svg` | Official glyph path from Commons `File:SmartThings Icon 2024.svg` |
| Spotify (added apps) | `spotify.svg` | CleanFrame / Simple Icons, vector |

Matching for added apps is by app ID or name (`knownMark()` in `main.js`): SmartThings, Spotify, Netflix, YouTube and Prime Video.
Other apps use the TV's own `iconPath` in the same slot. If the TV only provides the Tizen pinwheel placeholder
(dark or blue, detected by a 16x16 RGBA fingerprint against `tizen-placeholder-ref*.png`), the tile shows an ink monogram.

Some TVs return a placeholder, banner or unavailable icon path rather than usable artwork. Matching bundled marks keep recognised apps legible; unknown apps use their installed icon or a monogram fallback. This does not assume another TV's application IDs.
