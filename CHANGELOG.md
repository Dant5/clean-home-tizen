# Changelog

## 1.4.0 public preview

- Fresh installations start with one + tile and no preselected applications. Selecting an installed app fills that position and leaves another + until the nine-app limit.
- Hold Select on an existing Home tile to open its replacement picker. Short Select launches on release. Cancel, navigation, blur and suspend cannot complete a stale hold.
- Existing saved favourites, appearance and bindings remain authoritative; established configurations do not gain an extra + tile.
- Preserves the original photo/glass/clock design and the tested 1.3.9 shading cache.
- Adds generic unsigned release packaging, checksums, installation/recovery guidance, compatibility reporting and tests in Chromium 85/current Chromium.

The new first-run and long-press controls have browser coverage; physical-remote confirmation for those new controls is pending. Only the reference Q60B has launcher-core hardware evidence. No native Home/startup change is installed by the download.

## 1.3.9 reference-device milestone

Pre-rendered original shading reduced repeated startup gradient drawing on the Q60B. Two debug traces showed approximately 81–88% less aggregate raster-worker work. The owner subsequently reported prompt early-arrow response after a normal standby/wake. Existing app data and launcher preferences were preserved. This is not a universal startup-time guarantee.

Earlier design and implementation history belongs to Clean Home and CleanFrame; see the upstream credits and retained licences.
