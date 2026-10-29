# FeurTube

YouTube with Shorts hidden by default. Open a shared Short as one video in the regular player, without the swipe feed.

**Experimental.** A YouTube 21.39.525 build has been patched, signed and installed alongside stock YouTube on a test phone. Startup and feature testing are in progress. Premium behavior remains unverified. There is no public release APK.

FeurTube patches the Android app using [Morphe](https://github.com/MorpheApp/morphe-desktop) and [anddea's RVX patches](https://github.com/anddea/revanced-patches). [FeurStagram](https://github.com/jean-voila/FeurStagram) inspired the scope: useful features stay accessible; distracting surfaces start disabled.

The default policy hides the Shorts navigation button and shelves in Home, Search, Subscriptions, channels, history and related videos. It disables Shorts resume on startup and removes the Shorts launcher shortcut. Shared Shorts use the regular player. Empty Shorts launches are consumed.

Normal playback, accounts, subscriptions, history and Premium features are requirements. Premium parity remains unverified, including native offline downloads, background playback, PiP, casting and enhanced bitrate. Stream spoofing starts **off** to try the stock playback client first. Non-root sign-in uses GmsCore and may still affect compatibility. Keep stock YouTube installed during testing.

## Build

Linux or macOS, Python 3.11+, JDK 21, and Android SDK build-tools **34.0.0** are required. Set `JAVA_HOME` and `ANDROID_HOME`. Install the SDK tools with `sdkmanager 'build-tools;34.0.0'` if needed.

```sh
./feurtube bootstrap
./feurtube test
```

This verifies pinned downloads, compiles the Java extension and desktop patch, and produces `build/feurtube.mpp`. It uses prebuilt upstream patch code; it does not rebuild RVX or prove its binary matches its source. All release URLs, checksums and source revisions are in [upstream.lock.json](upstream.lock.json). The build needs no GitHub token.

Supply a complete, unmodified YouTube APK yourself:

| YouTube version | Upstream Android floor | FeurTube status |
| --- | --- | --- |
| 21.13.164 | Android 9 | Host tests only |
| 21.39.525 | Android 12L | Experimental; build and install verified; feature tests pending |

APKM, XAPK, APKS and split APK inputs are not supported. Other versions and unrecognized signing certificates are rejected. Accepted Google certificate fingerprints are pinned in the lock file. An older supported version remains an older client even though FeurTube does not select the app-version spoof patch.

Read a signing password from your terminal, then generate a persistent local key:

```sh
read -r -s FEURTUBE_KEYSTORE_PASSWORD
export FEURTUBE_KEYSTORE_PASSWORD
./feurtube keygen
./feurtube patch /path/to/youtube-21.13.164.apk
# For 21.39.525, add --experimental.
```

Back up `.cache/signing.p12` and its password. Updates require the same key. Use `--keystore /path/to/key.p12` for another key with alias `feurtube`. The tool refuses to overwrite an existing output; use `--output` for another destination.

The result is `dist/feurtube.apk`, installed separately as `app.feurtube.android`. Each attempt keeps a patch report and log under `build/patch-*`; a successful signed build also writes a JSON receipt beside the APK. These contain build evidence, not an Android test result.

Non-root builds require [ReVanced GmsCore](https://github.com/ReVanced/GmsCore/releases) for sign-in. Install and authenticate it yourself. FeurTube does not request credentials. Settings appear under YouTube settings as **FeurTube**; Shorts removal is already enabled on a fresh install.

## Development

Read [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md) for the hooks and [docs/HANDOFF.md](docs/HANDOFF.md) for current work. Record Android results in [docs/TESTING.md](docs/TESTING.md). The bundle currently targets the desktop CLI; importing it into an Android patch manager is unsupported.

GPL-3.0-only. Upstream notices are retained in [NOTICE](NOTICE); provenance is in [docs/UPSTREAM.md](docs/UPSTREAM.md). FeurTube is independent of Google, YouTube, FeurStagram, RVX and Morphe. Do not commit signing keys, account data or YouTube APKs.
