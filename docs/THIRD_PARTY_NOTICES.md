# Third-party notices

The root MIT licence covers CleanFrame's original code and documentation. Third-party material retains the terms below. Keep these notices and the adjacent licence texts when sharing source or a build.

## Fonts

| Material | Terms and source record |
| --- | --- |
| Manrope | SIL Open Font License 1.1; `app/assets/manrope-OFL.txt` |
| Geist and Newsreader | SIL Open Font License 1.1; licences beside the files in `app/assets/fonts/`, with exact sources and hashes in `app/assets/fonts/SOURCES.json` |
| Optional PP Neue Montreal, PP Mori and PP Pangram Sans | Proprietary. Binaries stay in ignored `.local/` storage and are excluded from Git and public exports. The optional local overlay requires the user's own permission to use and embed those files. |

The public app uses Manrope, Geist and Newsreader. A personal widget containing proprietary fonts must stay private. See [Pangram's licensing information](https://pangrampangram.com/pages/eula).

## Icons and trademarks

| Material | Provenance and terms |
| --- | --- |
| Simple Icons service marks | CC0; exact revisions and adaptations in `app/assets/icons/SOURCES.json` and `ADDITIONAL-SOURCES.json`. The CC0 text is retained beside the icons. |
| Disney+, ABC and SBS marks | [Custom Brand Icons](https://github.com/elax46/custom-brand-icons), MIT. The retained licence is `app/assets/icons/CUSTOM-BRAND-ICONS-LICENSE.txt`. ABC and SBS sources were replaced during the public-source review. Exact revisions, source files and extraction/recolour notes are in `SOURCES.json`. |
| Art, apps, settings and home outlines | Original CleanFrame drawings, covered by the project's MIT licence. |

Brand marks identify services. Their owners retain trademark rights; this project claims no endorsement or affiliation. The older Australian TV icon archive's GPL text is retained for historical provenance only; no current icon uses that archive.

## Photographs and derived materials

The fifteen photo pages were individually checked on 20 October 2026. Each displayed its credited author and free use under the [Unsplash License](https://unsplash.com/license). The [asset source register](asset-sources.md) links every page. Runtime paths are in `app/assets/wallpapers/SOURCES.json`.

Photographers retain their rights. Wallpapers, thumbnails, panel backgrounds and material fields derive from the credited photographs and retain their terms. The Unsplash licence permits copying, modification and distribution subject to its restrictions, including on selling unmodified images and building a competing image service.

## Development dependencies and exports

The on-demand QR encoder is [qrcode-generator by Kazuhiko Arase](https://github.com/kazuhikoarase/qrcode-generator), MIT, vendored from commit `83b7e8fe3fddd3b0368dbafd6ce56995bd25e3c8` (`js/dist/qrcode.js`, SHA-256 `79ec86f82856005b1c887905cfccfcfbec3821ca61c7fd5a952faa5f778f791c`). Its complete licence is in `app/assets/licenses/qrcode-generator-MIT.txt`. Codes are generated locally without a QR service. The test-only jsQR decoder retains its Apache-2.0 licence in the development dependency; it is not bundled in the widget.

Development dependencies retain the licences in their npm packages. They are not copied into the TV JavaScript runtime.

`npm run export:public` excludes private fonts and includes this notice and the root MIT licence. Preserve the included font and icon licence texts. Review [public release preparation](public-release.md) before publishing a repository or download.

## Q60B adaptation and standalone signer

Clean Home by chaosmanage/Kunal S is retained from the source revision in
`docs/upstream-sources.json`, building on Nathan Clark's CleanFrame MIT code.
The Q60B adaptation preserves that licence and the upstream asset notices.
The separate read-only diagnostic in `tools/home-inspection/`
adapts native query functions from the same MIT project, copyright 2026 Nathan
Clark, reviewed at revision `57415fdf5ffc2013b66bc98aca94e0963e0888be`.
It excludes the upstream setters and command-injection transport. Its source
notice and the root MIT licence must accompany any separately built diagnostic.
Bundled `*-lens.jpg` images are quarter-resolution blurred derivatives of the
same credited wallpaper photographs, prepared offline for the header focus glass.

`vendor/aerotizen/` and its reused signing/SDB tests derive from AeroTizen by
Hamza El Alaoui, MIT; its full licence is `vendor/aerotizen/LICENSE`. The standalone signer, SDB transport and inventory parser are vendored. No debloating or watcher tools are included in the widget. Separate native helper source is advanced research. HDMI source API usage was reviewed against tidyTizen and Samsung's
public TVWindow/SystemInfo documentation; implementation stays in our adapter.
Bing's optional daily photographs remain subject to their original photographers'
and Microsoft's rights; no Bing photograph is redistributed in this package.

## Favourite application artwork and catalogue filtering

Original Nuvio Legacy and Moonlight PNG artwork is bundled verbatim from their version-pinned open-source repositories so the four favourite icons can appear without a registry scan. The original PNG source files, full upstream GPL v3 licence texts and exact source revisions/hashes are in `app/assets/icons/favourites/`. Those images retain their original licences and trademarks. No Nuvio or Moonlight program code, accounts or pairing data is bundled. YouTube and Spotify retain the existing CC0 marks described above.

Consumer-app filtering is adapted from [arn0-tv](https://github.com/NelsonEU/arn0-tv/blob/b35c292e5bc63648cb8fef576bf5eacd9ea488d1/src/js/apps.js), copyright 2026 Arnaud Etienne, MIT. Its full licence is retained in `app/assets/licenses/arn0-tv-MIT.txt`. Filtering affects only this launcher's list; it never disables or removes an installed package.

## Separate native Home controller

`tools/home-control/` adapts native snapshot, readback and restoration ideas from AeroTizen by Hamza El Alaoui, MIT, reviewed at revision `c4b649b4fa22a43e19842f0f6d52acdfa69cc1d3`. The full licence is retained at `vendor/aerotizen/LICENSE`. The Q60B-specific policy, firmware guard and fake-platform tests are separate from the web widget. A private reviewed SDK runner uses AeroTizen's bounded staging/callback builder; addresses, original settings and execution receipts are excluded from Git. No AeroTizen watcher or debloating component is included.

The displayed Nuvio monochrome SVG adapts the same pinned Nuvio project's official symbol paths: gradients become white, transparent cutouts and the central play mark remain. It retains GPL v3 and the trademark; exact source/derivation hashes and changes are in `app/assets/icons/favourites/SOURCES.json`.

The displayed Moonlight monochrome SVG derives from the official Moonlight Qt symbol at pinned revision `ac296864ace96f51ad75f78b90644bdbca76c332`: grey backing removed and spokes made transparent. It has no wordmark. GPL v3, the official full licence and exact provenance are retained in `app/assets/icons/favourites/moonlight-symbol-LICENSE.txt` and `SOURCES.json`.

## Cached background shading

`app/assets/background-overlays/` contains transparent images rendered from the original MIT CleanFrame/Clean Home CSS, without photographs. They preserve the CSS shading for the fifteen bundled wallpaper appearances and two layouts; the generation script and source-input hashes are included. They retain the original code copyright and MIT notice.
