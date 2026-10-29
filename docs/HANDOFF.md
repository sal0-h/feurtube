# Handoff

Updated 2026-10-29. Goal: a public, maintainable FeurStagram-style YouTube patcher with Shorts disabled from first launch and shared Shorts in the regular player. Preserve normal YouTube and **all Premium features**. The user has Premium; replacing native downloads with an external downloader is not acceptable.

Published source: https://github.com/sal0-h/feurtube. [CI passes](https://github.com/sal0-h/feurtube/actions/runs/40965300379). Implemented: checksum-pinned CLI/RVX downloads, a compiled Java policy and extension, declared upstream patch dependencies, strict APK version/certificate/split checks, local persistent signing, patch reports and output receipts. Host tests passed, including real DEX mutation, referenced upstream API signatures and exclusion of compile-only test doubles. The CLI has loaded the combined bundle successfully. Two consecutive local builds produced identical bundles. No full APK patch or Android behavior has passed yet.

The phone is connected and authorized through host ADB. Sandboxed ADB cannot see USB devices; use the normal approval mechanism for host ADB. Model: S23 Ultra; Android 16/API 36; installed YouTube 21.43.523 is unsupported. GmsCore was not found. No package was installed or removed, and no account action was taken. The user was asked to download a standalone YouTube 21.39.525 APK to phone Downloads and leave it uninstalled. APKMirror returns HTTP 403 from this build environment. Check whether that download is now available before repeating the request.

Next:

1. Host tests pass after input certificate/split validation and settings overlay changes: seven Python checks, runtime/default tests, real upstream DEX mutation/serialization, API signature checks and Morphe loading. Keep these checks passing while testing an APK.
2. Source publication and CI are complete. Keep the public source current. Do not publish an APK release yet.
3. Obtain a complete supported stock APK. Verify its Google signing certificate, then patch without forcing compatibility. Do not modify or downgrade stock YouTube.
4. Build and install the separate FeurTube package. GmsCore installation and user-run sign-in are needed for account tests. Start with stream spoofing disabled. Determine whether normal playback works before making changes.
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
