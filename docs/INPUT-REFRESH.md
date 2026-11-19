# Refresh HDMI status when returning to an open input list

An HDMI chooser left open can display a device's old connection state after the TV resumes. Both the installed 1.3.9 lineage (`7d2109e`) and public main (`67090df`) refresh when opening the list and before switching, but do not refresh an already-open list on return.

## Implementation

Re-enumerate through the existing bounded public `VIDEOSOURCE` adapter only when an input panel is foregrounded. Overlapping foreground/resume events share one pending request. There is no timer, idle poll, native listener, helper, dependency or persistent setting.

Preserve focus by source type/number using the selection at completion, including movement made during the request. Preserve Back when the list length changes; if a selected port disappears, clamp to a remaining row or Back. An empty refreshed result leaves Back usable. Identical results do not replace the rows.

Ignore superseded results after Back, blur, hiding, native relaunch, leaving the panel or beginning another action. A failed/timed-out refresh keeps the last snapshot and remote focus; it does not open an asynchronous error dialog. Selecting a port still performs fresh source discovery before issuing a command. A Connected label is a snapshot, not proof of current signal or successful CEC wake.

No CSS, fonts, backgrounds, animations, layout, application identity, saved preferences, native Home/startup or existing recovery logic changes. The source-only rollback is a revert of this commit, with no data migration.

## Upstream comparison

The comprehensive area-by-area assessment is in [PR #21](https://github.com/Dant5/clean-home-tizen/pull/21), including its pinned-source review. This is a separate, independently authored follow-up using existing ES5/callback architecture. All four reviewed roots carry MIT licences; no upstream runtime/source assets were copied.

| Source, latest rechecked 19 November 2026 | Decision |
|---|---|
| [CleanFrame `845f332`](https://github.com/nthnclrk/CleanFrame/tree/845f332d083502fab39be49869052966103b564a) | Foreground input refresh solves a real gap; adapt the behavior with our existing UI. |
| [AeroTizen `de2cd03`](https://github.com/helalaou/AeroTizen/tree/de2cd03065620b18592f054395e01f258a22b3ed) | Its latest 3.3.2 commit changes release metadata only, wrapping the already reviewed IP Control diagnostics fix. Input listeners/naming and Continue Watching remain separately assessed; no IP Control subsystem is introduced. |
| [tidyTizen `bcb94c1`](https://github.com/ayala/tidyTizen/tree/bcb94c1a7788ab449eb626bd9b533b417c4ba4d8) | No newer source changes; no visual or native-viewer transplantation. |
| [arn0-tv `b35c292`](https://github.com/NelsonEU/arn0-tv/tree/b35c292e5bc63648cb8fef576bf5eacd9ea488d1) | No newer source changes; preserve existing Q60B Home mechanism instead of importing another model's native controls. |

## Compatibility, cost and qualification

This uses the same public discovery API already used on the Q60B, with no added permission. ES5 and packaged-engine checks cover older and newer browser generations. The added work is one bounded enumeration on a relevant foreground event, no polling on Home, and no extra render when source data is unchanged. Samsung-specific resume ordering and returned metadata still require physical Q60B/Tizen 6.5 / firmware 1720.7 confirmation.

Automated browser regressions cover status changes, source reordering, focus moved during discovery, Back preservation, duplicate events, unchanged rendering, failure, empty results and out-of-order callbacks after blur/hiding/Back. The actual unsigned widget is also exercised through the existing eight-engine harness. These tests mock Samsung APIs and do not establish HDMI signal, CEC or audio behavior.

After an approved same-identity update, leave Inputs open, sleep/wake a connected device or the TV, and verify refreshed status plus unchanged selected input. Check rapid Back, unplug/reconnect, HDMI handoff and audio without adjusting Samsung picture/sound settings. Do not claim physical success before that session. Deployment remains separate from DNS/privacy PR #20 and the late-handoff fix in PR #21.
