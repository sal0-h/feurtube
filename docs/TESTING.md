# Android validation

No complete FeurTube APK has been tested yet. [Host tests passed in CI on 2026-10-29](https://github.com/sal0-h/feurtube/actions/runs/40965300379): runtime policy/defaults, released RVX DEX mutation and serialization, Morphe bundle loading, compile-only stub exclusion, upstream API signatures, dependency checksum rejection, input certificate/version rejection, resource overlay and patch selection. Consecutive local builds produced the same policy bundle hash.

Test device available: Samsung S23 Ultra, Android 16 (API 36). Stock YouTube is 21.43.523, outside the pinned compatibility list. No device identifier or account data belongs in this file.

For each device run, record the YouTube version, input APK SHA-256, FeurTube commit, output signing certificate SHA-256, Android version and sanitized results. Keep stock YouTube installed. Do not mark a feature passed because its setting exists.

| Check | Expected result | Status |
| --- | --- | --- |
| Fresh install and cold start | Separate FeurTube app opens without a crash | Pending |
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

Use `adb install -r dist/feurtube.apk` only after a successful verified build. Do not uninstall stock YouTube or clear either app's data. The user handles sign-in. App-targeted UI inspection must avoid account pages and private content in published artifacts.
