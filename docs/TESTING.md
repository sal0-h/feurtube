# Android validation

A complete APK was patched, signed, verified and installed on 2026-10-29. The user subsequently confirmed background playback, no visible Shorts, and downloaded videos playing offline in FeurTube's own Downloads. These are manual results from one device, not a full Premium compatibility result. [Host tests passed in CI](https://github.com/sal0-h/feurtube/actions/runs/40966214573), including the report-format regression checks and rebuilt-APK verifier.

Test device available: Samsung S23 Ultra, Android 16 (API 36). Stock YouTube is 21.43.523, outside the pinned compatibility list. No device identifier or account data belongs in this file.

Test build: commit `f1916dd`, YouTube 21.39.525 standalone APK. Input SHA-256: `6ee08e8a686dbd006264daa64d49443d7d215127cc6fc5f5039339cd9d13e807`. Output SHA-256: `b81e2cfcf47e28ffc2243c16e604f8ed136d1e9568cd8b14c54c098b9d7913b7`. Signing certificate SHA-256: `20d53e9c1932da1a8225db7a9186d56865800e1473629a834f531e88b1413030`. Original Google signing certificates were verified before patching. The rebuilt APK was checked for the injected defaults and Shorts-redirect hooks before signing.

GmsCore: official ReVanced release `v0.3.13.2.250932`, asset `app.revanced.android.gms-250932004-signed.apk`, SHA-256 `62119f040d629a9cd3225f280649a464936730c6466cafb5b9dd5ded14269a65`. Release digest and APK signature verified; installation succeeded. No account was added by the agent. Stock YouTube and its data remain in place.

For each device run, record the YouTube version, input APK SHA-256, FeurTube commit, output signing certificate SHA-256, Android version and sanitized results. Keep stock YouTube installed. Do not mark a feature passed because its setting exists.

| Check | Expected result | Status |
| --- | --- | --- |
| Install and initial startup | Separate FeurTube app opens and is usable | Pass: installed; user exercised the app |
| Google account / Premium | User signs in; existing subscription recognized | Background playback and native downloads user-confirmed; account UI not inspected |
| Shorts visibility in normal use | Shorts absent while ordinary YouTube remains usable | Pass: user reports no Shorts; individual surfaces below still need checks |
| Home, Search, Subscriptions, channels, history | Shorts shelves absent; normal videos remain | Pending |
| Bottom navigation | No Shorts button | Pending |
| Direct `/shorts/ID` link | Regular video page rather than the Shorts player | Pass: agent observed the recent vertical NASA Short `myZ9kn9MIWQ` in the regular player |
| Short `youtu.be` link and in-app Short | Regular player | Pending |
| Android default link routing | Links open in FeurTube when selected by the user | Pending; direct test used an explicit package; phone-wide defaults unchanged |
| Shorts launcher shortcut / empty launch | No Shorts feed | Pending |
| Relaunch after a Short | No Shorts resume | Pending |
| Normal playback | Seek, captions, speed, audio tracks and live video work | Pending |
| Background playback | Playback continues outside the app | Pass: user report |
| Lock-screen controls | Pause, resume and seek work while locked | Pending |
| Picture-in-picture | Video continues after leaving the app | Pending |
| Native Premium downloads | Download and play offline using YouTube's own library | Pass: user explicitly confirmed offline playback in FeurTube's own Downloads |
| Smart Downloads / downloaded playlist | Existing Premium behavior retained | Pending |
| Premium quality / queue / continue watching | Available as in stock for the same account and content | Pending |
| Casting | Existing receiver and account flow works | Pending |
| Library and history | Subscriptions, playlists and playback history sync | Pending |
| Upgrade with the same signing key | Installs over FeurTube and retains preferences | Pending |

Shared-link test: with the user ready and no personal playback interrupted, Android opened `https://www.youtube.com/shorts/myZ9kn9MIWQ` explicitly in `app.feurtube.android`. The agent observed NASA's recent vertical "2026 Solar Eclipse @ 50,000 Feet" video playing above the normal title/channel/action area and standard watch-page content. This verifies the regular-player route for that direct Shorts URL. It does not verify every navigation path or a swipe gesture. An older `/shorts/O1gj-MMjtqc` URL also opened normally, but that result alone would not establish handling of a genuine Short.

The initial capture gate was too narrow: Morphe renamed the foreground activity to `app.feurtube.android.morphe_original_5`, so requiring the original `watchwhile.MainActivity` name rejected a valid FeurTube screen. Checking the exact foreground package resolved this. No application-code change was needed. Screenshots stayed private and were removed after inspection.

Test native downloads separately from external downloaders. They are different features. If a workaround enables playback but loses a Premium feature, record that as a regression. Do not silently enable stream spoofing, replace a Premium feature, or count another app as a pass.

Use `adb install -r dist/feurtube.apk` only after a successful verified build. Do not uninstall stock YouTube or clear either app's data. The user handles sign-in. Check the focused package before capturing a test screen; never capture authentication forms or other apps. Check that UI dumps succeeded, since a timeout can leave an old file behind. Keep all captures and raw logs private.
