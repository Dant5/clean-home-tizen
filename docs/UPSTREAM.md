# Credits and provenance

This is an independent adaptation of [chaosmanage’s Clean Home](https://github.com/chaosmanage/samsung-tv-launcher), built on **CleanFrame by Nathan Clark**. The photographic layout, glass treatment, clock, focus effects and much of the original implementation remain. This project claims no ownership of that design or endorsement by Samsung or the app brands.

The Q60B integration adds discovered/manual application IDs, four-service branding, local recovery/error handling, Tizen 6.5 compatibility fixes and measured rendering improvements. The public preview starts without favourites and adds a progressive + picker and long-press replacement. It retains the same application identity so existing configurations can be preserved on a same-author upgrade.

The public repository is a clean source snapshot. The private development history, device addresses, signing credentials, per-TV native baselines, diagnostic recordings and personal signed packages are not included. Original licences, notices, source revision records and asset credits are preserved. [Reviewed source revisions](upstream-sources.json) · [third-party notices](../THIRD_PARTY_NOTICES.md).

AeroTizen’s MIT standalone signer and supporting transport/parser tests are retained under `vendor/aerotizen/`. Consumer-app filtering adapts arn0-tv’s MIT implementation. HDMI usage was reviewed against tidyTizen and Samsung’s public APIs. Native Home/controller sources are separate advanced research; no debloating or watcher is bundled.

Fonts are Manrope, Geist and Newsreader under SIL OFL. Photographs and derivatives retain their credited Unsplash terms. Service marks retain their owners’ rights; Nuvio/Moonlight symbol derivatives retain their adjacent GPL notices/source records. See [photo credits](asset-sources.md), [icon sources](ICON-SOURCES.md) and the licences next to the files.
