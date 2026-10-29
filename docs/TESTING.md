# Android validation

A complete APK was patched, signed, verified and installed on 2026-10-29. First launch reached Android's notification permission prompt with the app process running. Startup and feature testing continue after that prompt. [Host tests passed in CI](https://github.com/sal0-h/feurtube/actions/runs/40966214573), including the report-format regression checks and rebuilt-APK verifier. Premium compatibility has not passed.

Test device available: Samsung S23 Ultra, Android 16 (API 36). Stock YouTube is 21.43.523, outside the pinned compatibility list. No device identifier or account data belongs in this file.

Test build: commit `f1916dd`, YouTube 21.39.525 standalone APK. Input SHA-256: `6ee08e8a686dbd006264daa64d49443d7d215127cc6fc5f5039339cd9d13e807`. Output SHA-256: `b81e2cfcf47e28ffc2243c16e604f8ed136d1e9568cd8b14c54c098b9d7913b7`. Signing certificate SHA-256: `20d53e9c1932da1a8225db7a9186d56865800e1473629a834f531e88b1413030`. Original Google signing certificates were verified before patching. The rebuilt APK was checked for the injected defaults and Shorts-redirect hooks before signing.

GmsCore: official ReVanced release `v0.3.13.2.250932`, asset `app.revanced.android.gms-250932004-signed.apk`, SHA-256 `62119f040d629a9cd3225f280649a464936730c6466cafb5b9dd5ded14269a65`. Release digest and APK signature verified; installation succeeded. No account was added by the agent. Stock YouTube and its data remain in place.

For each device run, record the YouTube version, input APK SHA-256, FeurTube commit, output signing certificate SHA-256, Android version and sanitized results. Keep stock YouTube installed. Do not mark a feature passed because its setting exists.

| Check | Expected result | Status |
| --- | --- | --- |
| Fresh install and cold start | Separate FeurTube app opens without a crash | Installed; first launch reached notification prompt; full startup pending |
| Google account / Premium | User signs in; existing subscription recognized | Pending |
| Home, Search, Subscriptions, channels, history | Shorts shelves absent; normal videos remain | Pending |
| Bottom navigation | No Shorts button | Pending |
| Shared `/shorts/ID`, short link and in-app Short | Regular player; no swipe feed | Pending |
| Shorts launcher shortcut / empty launch | No Shorts feed | Pending |
| Relaunch after a Short | No Shorts resume | Pending |
| Normal playback | Seek, captions, speed, audio tracks and live video work | Pending |
| Background playback and lock screen | Premium playback continues; controls work | Pending |
| Picture-in-picture | Video continues after leaving the app | Pending |
| Native Premium downloads | Download and play offline using YouTube's own library | Pending |
| Smart Downloads / downloaded playlist | Existing Premium behavior retained | Pending |
| Premium quality / queue / continue watching | Available as in stock for the same account and content | Pending |
| Casting | Existing receiver and account flow works | Pending |
| Library and history | Subscriptions, playlists and playback history sync | Pending |
| Upgrade with the same signing key | Installs over FeurTube and retains preferences | Pending |

Test native downloads separately from external downloaders. They are different features. If a workaround enables playback but loses a Premium feature, record that as a regression. Do not silently enable stream spoofing, replace a Premium feature, or count another app as a pass.

Use `adb install -r dist/feurtube.apk` only after a successful verified build. Do not uninstall stock YouTube or clear either app's data. The user handles sign-in. Check the focused package before capturing a test screen; never capture authentication forms or other apps. Check that UI dumps succeeded, since a timeout can leave an old file behind. Keep all captures and raw logs private.
