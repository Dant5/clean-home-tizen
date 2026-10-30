# Optional TV report receiver

These are the authored intake handler, validation schema and database migration used by [Clean Home TV feedback](https://clean-home-feedback.perkymule6.chatgpt.site). Hosting credentials, provider configuration and the private database are not in this repository. The code is MIT licensed.

The hosted service accepts anonymous, explicit TV submissions. It has **no public report-reading endpoint**. The maintainer reviews records through the hosting provider's authenticated database tools. A receipt identifies a submission; it does not grant public read access. Reports are not automatically posted to GitHub or forwarded to an AI chat.

`GET /api/reports` returns service health only. `OPTIONS` permits credential-free cross-origin POSTs from packaged TV apps. `POST` accepts the documented TV-report or setup-report schema, rejects extra fields and bounds the body, versions, text and error counts. It never stores request headers, internet addresses, identifiers, app inventories, screenshots or raw messages. SQL uses bound parameters. There is no shared client secret in the TV app.

The D1 table contains only a random per-report receipt, received timestamp and allowlisted JSON. Incoming submissions remove records older than 90 days. Atomic global limits allow 30 per minute and 500 per day; these are preview service limits, not a verified count of unique televisions. There is no per-TV tracking or automatic retry. No fixed deletion time is guaranteed when there are no incoming submissions.

For self-hosting, use a Cloudflare Worker-compatible environment with a `DB` D1 binding. Apply `schema.sql` as a migration, mount the exported GET/OPTIONS/POST handler at `/api/reports`, and serve the public privacy explanation. The hosted version uses Vinext route handling. Keep database access private. A custom receiver also needs a matching endpoint and exact network origin in the TV app's manifest; the distributed client deliberately accepts only the project's configured receiver.

The public intake is not proof that a report came from a real TV. Mark synthetic test records by model `CLEAN_HOME_TEST`; exclude them from compatibility findings. Review exact model, firmware, app version and observed behaviour before updating the support chart. [Report fields and privacy](../../docs/TV-REPORTS.md).

Setup report schema 2 adds fixed capability-stage results to the same private inbox. Schema 1 TV reports remain compatible. Neither schema permits raw messages, app inventories, recovery originals or unique device/network identifiers.
