# Privacy

Clean Home has no analytics, advertising trackers or user accounts. It does not use the camera or microphone.

- **Saved on your TV:** shortcuts, settings, manually entered app IDs and a small installed-app list. Clean Home discovers and opens apps using Samsung’s public APIs. It cannot read their private accounts, settings or pairings.
- **Daily photos:** on by default. Bing/Microsoft receives normal image requests and can see your public internet address. Turn them off in **Settings → Background → Daily photo**. Bundled photos work offline. The default Bing region is `en-AU`; only the chosen photo’s URL/date is saved in app storage.
- **Weather:** off by default. Developers enabling it with a location in `app/device-config.js` send that location to Open-Meteo. Your location is not inferred.
- **Share TV report:** optional. Review model, firmware, Tizen/browser/app versions, app surface size, basic loading status, error totals and the last TV error category/code. **Send** uploads these details to the project's [feedback receiver](https://clean-home-feedback.perkymule6.chatgpt.site), where they remain in a private maintainer database. There are no background uploads. Reports exclude installed apps/IDs, accounts, addresses, serial numbers, DUIDs, credentials, pictures and raw error messages. The hosting provider sees normal request information, including your internet address; the report database does not store it. Reports older than 90 days are pruned when new feedback arrives. Confirmed compatibility findings may appear in the public support chart.
- **Phone fallback:** **Use phone** prepares a QR code locally. Scanning sends those report details to GitHub in a prefilled issue; submitting publishes it and requires a GitHub account. This is optional. [Details and manual reporting](TV-REPORTS.md).
- **Optional Home Setup:** originals stay in your computer's private user-data folder, bound to a hash of the TV's developer identity. The setup tool uses the local network and never uploads those originals or accesses your signing certificates. They are not app-data backups.

Installation tools and the apps you open have their own privacy policies.
