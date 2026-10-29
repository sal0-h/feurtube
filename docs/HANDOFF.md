# Handoff

Updated 2026-10-29. Goal: a public, maintainable FeurStagram-style YouTube patcher with Shorts disabled from first launch and shared Shorts in the regular player. Preserve normal YouTube and **all Premium features**. The user has Premium; replacing native downloads with an external downloader is not acceptable.

Published source: https://github.com/sal0-h/feurtube. [CI passes](https://github.com/sal0-h/feurtube/actions/runs/40966214573). Implemented: checksum-pinned CLI/RVX downloads, a compiled Java policy and extension, declared upstream patch dependencies, strict APK version/certificate/split checks, local persistent signing, patch reports and output receipts. Nine Python checks plus Java/DEX/loader tests pass. A complete YouTube 21.39.525 APK has now been patched, signed, verified and installed. Feature and Premium tests are still pending.

The phone is connected and authorized through host ADB. Sandboxed ADB cannot see USB devices; use the normal approval mechanism for host ADB. Model: S23 Ultra; Android 16/API 36; stock YouTube 21.43.523 remains installed. The user downloaded the standalone YouTube 21.39.525 APK; it is copied to `.cache/inputs/youtube-21.39.525.apk`. APKMirror returns HTTP 403 here; no more download is needed. Official ReVanced GmsCore `v0.3.13.2.250932` and our separate FeurTube package are now installed. Both installs returned Success. First FeurTube launch reached Android's notification permission prompt. The user was told to choose their preferred option. The app process stayed running afterward, but a subsequent UI dump timed out, so full startup is not verified. The user is being asked to open FeurTube and signal readiness for testing, optionally after signing in. No account action was taken by the agent. Let the user handle Google sign-in.

The first APK patch succeeded but our report validator incorrectly expected dependency names in `appliedPatches`. Morphe reports selected roots only. Commit `f1916dd` fixes the validator, adds regression tests and checks the hooks in the rebuilt APK before signing. The second run succeeded fully: `dist/feurtube.apk` and `dist/feurtube.json`; report/log under `build/patch-ds_d5i8l/`. The receipt's `android_tested` remains false until feature validation. Sanitized build identifiers are in `docs/TESTING.md`.

Next:

1. Wait for the user's readiness signal, then inspect FeurTube. Confirm it reaches its own UI. Check the focused package before capturing: do not capture other apps or authentication forms. UI dumps belong only under `.cache`, never in Git. A failed dump may leave a stale file; do not use it. Local UI captures from this run were removed.
2. Source publication and CI are complete. Keep the public source current. Do not publish an APK release yet.
3. The APK and GmsCore dependency are already installed. Do not repeat setup or ask the user to download again. For another build use a new `--output` path; install over FeurTube with the same key using `adb install -r`.
4. Let the user sign in through GmsCore on the phone when ready. Start with stream spoofing disabled. Determine whether normal playback works before making changes.
5. Run `docs/TESTING.md`, including Premium native downloads and background playback. If preserving Premium conflicts with the patching architecture, report the evidence and discuss that constraint; do not promise parity.
6. Check settings on-device. The resource overlay replaces the Shorts player-type selector with a fixed explanation; inherited settings still need a usability review.

Local commands:

```sh
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export ANDROID_HOME="$PWD/.cache/android-sdk"
./feurtube test
```

The local `.cache/android-sdk/build-tools/34.0.0` is a copy of the installed SDK tools: the system copies are readable but not executable by this sandbox user. Other machines should use their own SDK. A local signing key was generated at `.cache/signing.p12`; its random password is in `.cache/signing-password` with mode 0600. Load it into the environment inside a subprocess without printing it. Back up both privately. Neither is tracked. Upstream reference checkouts are under `/tmp/feurtube-{anddea,feurstagram,patcher,desktop}`; they are disposable. All durable implementation is in this repository. `.cache` and `build` are disposable except for signing material.

The user may move the task to another Codex session via `codex-dukhan`. Resume from this file and the Git history. Read `AGENTS.md`; keep claims tied to evidence and preserve upstream credits.
