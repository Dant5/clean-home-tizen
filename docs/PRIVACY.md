# Privacy

Clean Home has no analytics, advertising trackers or user accounts. It does not use the camera or microphone.

- **Saved on your TV:** shortcuts, settings, manually entered app IDs and a small installed-app list. Clean Home discovers and opens apps using Samsung’s public APIs. It cannot read their private accounts, settings or pairings.
- **Daily photos:** on by default. Bing/Microsoft receives normal image requests and can see your public internet address. Turn them off in **Settings → Background → Daily photo**. Bundled photos work offline. The default Bing region is `en-AU`; only the chosen photo’s URL/date is saved in app storage.
- **Weather:** off by default. Developers enabling it with a location in `app/device-config.js` send that location to Open-Meteo. Your location is not inferred.
- **Share TV report:** optional. The TV prepares a QR code locally with model, firmware, Tizen/browser/app versions, app surface size, basic loading status, error totals and the last TV error category/code. It excludes installed apps/IDs, accounts, addresses, serial numbers, DUIDs, credentials, pictures and raw error messages. Scanning opens a prefilled GitHub issue on your phone, sending those report details to GitHub. Submitting publishes it; a GitHub account is required. Nothing is automatically uploaded by the TV. [Details and manual reporting](TV-REPORTS.md).

Installation tools and the apps you open have their own privacy policies.
