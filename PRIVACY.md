# Privacy

Preferences, selected app IDs, appearance, manual bindings and a bounded installed-app catalogue are stored locally in this app’s Tizen storage. The launcher uses the TV’s public application APIs to discover and open installed apps. It does not read their isolated accounts, playback configuration or pairing databases.

Bing daily pictures are on by default and optional: Settings → Background → Daily photo turns them off. Bing receives ordinary HTTPS requests for its archive and image URLs, using the market in `app/device-config.js` (initially `en-AU`). Bing/Microsoft may see the network’s public address. Only the selected URL/date is persisted by this app; the live picture and generated header material are held in memory/browser cache. Bundled wallpapers work offline.

Weather is disabled. Enabling it with an explicit location in `app/device-config.js` sends that location to Open-Meteo. No location is inferred from your network.

There is no telemetry server, analytics identifier, account system, camera capture or microphone recording. There is no Home Assistant requirement or background Home watcher. The normal widget does not expose a network-control endpoint. Temporary Web Inspector access, if deliberately enabled by a developer, should remain on a trusted LAN and be closed after testing.

Diagnostics can show model/firmware, user agent and installed-app metadata. Review/redact information before sharing. Do not post DUIDs, serial numbers, addresses, tokens, signing profiles, private recovery snapshots or account screens. Third-party streaming apps and installation tools have their own privacy policies.

Public-source and release checks reject literal device/network addresses, hardware identifiers, local user paths and signing material. Test fixtures use loopback or reserved documentation addresses and never contact a TV. Image checks flag location, owner and camera-identifier metadata. These checks supplement manual review and secret scanning; they cannot identify every possible kind of private content.
