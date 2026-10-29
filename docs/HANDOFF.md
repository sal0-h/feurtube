# Handoff

Updated 2026-10-29. Goal: a public, maintainable FeurStagram-style YouTube patcher with Shorts disabled from first launch and shared Shorts in the regular player. Preserve normal YouTube and **all Premium features**. The user has Premium; replacing native downloads with an external downloader is not acceptable.

Published source: https://github.com/sal0-h/feurtube. [CI passes](https://github.com/sal0-h/feurtube/actions/runs/40966214573). Implemented: checksum-pinned CLI/RVX downloads, a compiled Java policy and extension, declared upstream patch dependencies, strict APK version/certificate/split checks, local persistent signing, patch reports and output receipts. Nine Python checks plus Java/DEX/loader tests pass. The installed YouTube 21.39.525 build works in the first device test: the user confirms background playback, native offline downloads and no visible Shorts. The agent observed a recent vertical Short opening in the regular player. Other devices, other entry points and remaining Premium features are unverified.

The phone was connected and authorized through host ADB. Sandboxed ADB cannot see USB devices; use the normal approval mechanism for host ADB. Model: S23 Ultra; Android 16/API 36; stock YouTube 21.43.523 remains installed and its data was not changed. The standalone source APK is cached at `.cache/inputs/youtube-21.39.525.apk`; no new download is needed. Official ReVanced GmsCore `v0.3.13.2.250932` and separate package `app.feurtube.android` are installed. The user handled setup and authentication. Do not repeat sign-in, clear app data or change stream spoofing.

The first APK patch succeeded but our report validator incorrectly expected dependency names in `appliedPatches`. Morphe reports selected roots only. Commit `f1916dd` fixes the validator, adds regression tests and checks the hooks in the rebuilt APK before signing. The second run succeeded fully: `dist/feurtube.apk` and `dist/feurtube.json`; report/log under `build/patch-ds_d5i8l/`. Build receipts always initialize `android_tested` to false; current device results live separately in `docs/TESTING.md`, together with sanitized build identifiers.

Latest user feedback: "Background play works, downloads work, no shorts!" They explicitly confirmed offline playback in FeurTube's own Downloads. The user then authorized a brief hands-off shared-link test. Direct VIEW intent `https://www.youtube.com/shorts/myZ9kn9MIWQ` opened NASA's recent vertical "2026 Solar Eclipse @ 50,000 Feet" Short in the regular watch page, observed by the agent. The test used an explicit package, so default Android link routing remains untested. Earlier capture attempts failed because they required an original activity name; the actual foreground alias is `app.feurtube.android.morphe_original_5`. This was an observation-gate issue, not an app crash. No application code changed. Test captures were removed; leave the phone with the user now.

Next:

1. Core first-device checks passed as recorded in `docs/TESTING.md`. Further device control should be coordinated with the user. Do not repeat the completed setup or tests without a reason.
2. Source publication and CI are complete. Keep the public source current. Do not publish an APK release yet.
3. The APK and GmsCore dependency are already installed. Do not repeat setup or ask the user to download again. For another build use a new `--output` path; install over FeurTube with the same key using `adb install -r`.
4. User-tested Premium background playback and native offline downloads pass. Do not repeat authentication or change stream spoofing. The stock-client default is working in this test so far.
5. For broader validation, continue pending cases in `docs/TESTING.md`: other Shorts entry points, default-link association, detailed shelf coverage, PiP, casting, Premium quality, lock-screen controls and updates. Label user reports separately from agent observations; do not generalize one-device success to full Premium parity.
6. Check settings on-device. The resource overlay replaces the Shorts player-type selector with a fixed explanation; inherited settings still need a usability review.

Local commands:

```sh
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export ANDROID_HOME="$PWD/.cache/android-sdk"
./feurtube test
```

The local `.cache/android-sdk/build-tools/34.0.0` is a copy of the installed SDK tools: the system copies are readable but not executable by this sandbox user. Other machines should use their own SDK. A local signing key was generated at `.cache/signing.p12`; its random password is in `.cache/signing-password` with mode 0600. Load it into the environment inside a subprocess without printing it. Back up both privately. Neither is tracked. Upstream reference checkouts are under `/tmp/feurtube-{anddea,feurstagram,patcher,desktop}`; they are disposable. All durable implementation is in this repository. `.cache` and `build` are disposable except for signing material.

The user may move the task to another Codex session via `codex-dukhan`. Resume from this file and the Git history. Read `AGENTS.md`; keep claims tied to evidence and preserve upstream credits.
