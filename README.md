# FeurTube

YouTube with Shorts hidden by default. Shared Shorts open in the regular video player.

Uses [anddea's RVX patches](https://github.com/anddea/revanced-patches) and [Morphe](https://github.com/MorpheApp/morphe-desktop), with a small Java policy for defaults and navigation. Inspired by [FeurStagram](https://github.com/jean-voila/FeurStagram).

Experimental. Tested on a Samsung S23 Ultra running Android 16 with YouTube 21.39.525: Shorts hiding, shared Shorts in the regular player, Premium background playback, native offline downloads and default link routing. Other devices and full Premium compatibility are untested. No public APK release.

[Website](https://sal0-h.github.io/feurtube/) · [Setup guide](https://sal0-h.github.io/feurtube/guide.html) · [Releases and legal considerations](https://sal0-h.github.io/feurtube/distribution.html)

## Build

Requires Python 3.11+, JDK 21 and Android SDK build-tools **34.0.0** on Linux or macOS. Set `JAVA_HOME` and `ANDROID_HOME`.

Supply a standalone, Google-signed YouTube APK: **21.13.164** (Android 9+) or **21.39.525** (Android 12L+, experimental). Split APKs and APKM/XAPK/APKS bundles are unsupported.

```sh
./feurtube bootstrap
./feurtube test

read -r -s FEURTUBE_KEYSTORE_PASSWORD
export FEURTUBE_KEYSTORE_PASSWORD
./feurtube keygen
./feurtube patch /path/to/youtube-21.39.525.apk --experimental
```

Output: `dist/feurtube.apk`, package `app.feurtube.android`. Logs and patch reports go under `build/patch-*`; a build receipt is written beside the APK. Use `--output` for another destination; existing files are not overwritten.

Back up `.cache/signing.p12` and its password privately. Updates need the same key. To use another key with alias `feurtube`, pass `--keystore /path/to/key.p12`.

## Install

Install [ReVanced GmsCore](https://github.com/ReVanced/GmsCore/releases), then the FeurTube APK. GmsCore is a separate microG-based Google-services implementation used for sign-in; it runs alongside Google Play Services and handles account authentication. Settings appear in the app under **FeurTube**. Shorts hiding is enabled on a fresh install; stream spoofing defaults to off.

For shared links, open Android **Settings → Apps → FeurTube → Set as default / Open by default**. Enable **Open supported links** for `youtube.com`, `www.youtube.com`, `m.youtube.com` and `youtu.be`. If stock YouTube owns those links, disable its supported-link handling first. Removing YouTube alone does not assign its links to FeurTube.

## Code

[feurtube](feurtube) downloads the pinned tools, compiles the extension with `javac` and D8, applies the patches, verifies the rebuilt hooks and signs the APK. Downloads are SHA-256 pinned in [upstream.lock.json](upstream.lock.json); upstream binaries are not rebuilt from source. The patch bundle targets the desktop CLI.

[FeurTubePatch.java](patches/src/app/feurtube/patches/FeurTubePatch.java) hooks RVX's settings constructor and Shorts navigation handler. [ShortsPolicy.java](extension/src/app/feurtube/extension/ShortsPolicy.java) supplies the defaults and regular-player redirect. RVX provides YouTube fingerprints, component filtering and GmsCore integration.

GPL-3.0-only. Preserve [LICENSE](LICENSE), [NOTICE](NOTICE) and upstream credits. Keep APKs, signing keys and account data out of Git.

The buildless site lives in `site/` and deploys to GitHub Pages on changes to `main`. Preview it with `python3 -m http.server --directory site 8000`.
