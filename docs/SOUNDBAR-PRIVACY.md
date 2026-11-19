# Q930D privacy qualification

The soundbar is a second protected client of the **same** AdGuard companion, not another TV application or background watcher. Combined statistics are the dashboard default; the View control distinguishes TV and soundbar activity. An unconfigured device is labelled unconnected, not assigned invented zero statistics. Controls switch/pause blocking for both configured devices, with that scope stated on screen.

## What is established

The owner's network has a reachable **Q-Series Soundbar** endpoint with its own address and interface identity, separate from the Q60B. A read-only Samsung local metadata request reports the 2024 `24_MT8532_AISPK` platform and soundbar firmware family. The endpoint does not expose a full retail HW-Q930D model code; the owner's physical model identification supplies that part of the association. Private addresses, MACs and raw metadata remain outside Git.

This proves a separate LAN connection. It does **not** prove which outbound DNS names it uses, that it is currently uploading telemetry, or that the TV's DNS controls its traffic. No soundbar settings, input, volume, microphone, account, firmware or network configuration were changed during discovery. Its DNS/Internet traffic needs separately attributed observation after a supported routing method is approved. Do not root it, enroll a new SmartThings cloud account or reuse TV developer tooling against it.

[Samsung's Australian Q930D specification](https://www.samsung.com/au/audio-devices/soundbar/q930d-black-hw-q930d-xy/) documents Wi-Fi/SmartThings, built-in Alexa, casting/Spotify Connect and HDMI eARC/Q-Symphony. These are functions to preserve, not telemetry to disable by service name. Do not filter multicast discovery, block its whole Internet access or change the existing HDMI connection as an ad-blocking shortcut.

## DNS routing

1. Privately match the endpoint and active MAC to the router's current lease; distinguish Wi-Fi/Ethernet interfaces and save original lease/reservation/DNS values.
2. Check the existing router UI for a **per-reservation DNS Server (Optional)** field. [ASUS documents this feature](https://www.asus.com/us/support/faq/1000906/), but features vary by model/firmware. Read-only inspection confirmed the field on the reference RT-AC88U / 3.0.0.4.386_48322; lease adoption is not yet tested. A DHCP IP reservation alone does not change DNS.
3. If supported, propose only two explicit reservation entries, keeping current addresses and setting only their DNS to the Dell. Wait for approval before applying. Renew only the affected device connection; verify actual DNS requests under its own IP rather than a shared router/proxy address.
4. If unsupported, do not set global DHCP/WAN DNS or flash router firmware. No documented soundbar-local DNS setter has been established in this work. Keep soundbar routing pending and present a separately reviewed device-only alternative. An unimplemented route must not display protected status.

Use the conservative Light + Samsung lists with SmartThings/account/update/casting compatibility exceptions and no explicit update blocks. Shared list membership is not evidence a domain is used by this soundbar. If a service fails, pause the dedicated filter, retest the same function and identify the specific domain before making an allow rule. Do not broadly whitelist/blacklist all Samsung cloud services based on names.

## Microphone and voice assistant

DNS filtering does **not** disable microphones. The dashboard deliberately does not claim to read the soundbar's microphone/assistant state.

- Supported physical control: Samsung identifies the **Mic On/Off** button at the far right of the soundbar's top panel. A red indicator means the microphone is disabled. Use the button to change it back. [Samsung microphone indicator guidance](https://www.samsung.com/my/support/tv-audio-video/red-led-light-appears-on-samsung-soundbar-or-music-frame/).
- Microphone-dependent audio functions are a separate trade-off: Samsung describes SpaceFit Sound Pro as using the soundbar microphone, and Active Voice Amplifier as analysing external noise. Do not claim muting preserves every adaptive feature without a physical test. [Samsung sound-control guidance](https://www.samsung.com/au/support/tv-audio-video/setting-sound-control-on-the-q-series-soundbar/).
- For disabling only assistant integration, inspect the existing SmartThings soundbar card's device/voice-assistant settings for a supported Alexa sign-out/unlink option. Menu availability and current enrollment are not verified on this owner's app/firmware. Do not delete the soundbar, reset it, disconnect the Samsung account, or present another model's community instructions as Q930D proof. No assistant account change has been made.

A later owner check should record only on/off/available results, with no passwords, tokens, voice recordings or account details. If mute or sign-out is requested, verify the red indicator/assistant behavior separately from DNS counters and test audio afterward. Local playback and eARC are not proof that SmartThings/firmware paths still work.

## Required physical/network checks after approval

- Distinct TV and soundbar DNS queries and blocks; totals sum correctly, and another household client is denied by the dedicated resolver.
- SmartThings discovery, current settings access and ordinary control without re-pairing.
- Normal HDMI eARC audio, Q-Symphony, volume/CEC, rear/subwoofer audio and audio after standby/wake. Do not change picture/sound tuning to make a DNS test pass.
- Existing Spotify Connect/casting modes the owner uses, and update-check connectivity without installing firmware.
- DNS bypass/fallback observations for **each** device; TV results cannot qualify the soundbar.
- Pause/resume and restoration of only the affected original DHCP/DNS values; reconnect and retest. Keep existing pairing and accounts.
