# Working on FeurTube

Read `docs/HANDOFF.md` before continuing. Keep it current when stopping or handing off.

- Keep the scope on Shorts removal and preserving normal YouTube behavior, including paid Premium features. Keep stock YouTube installed during tests. Do not clear its data, uninstall updates, change accounts, root the phone or disable device security to make a test pass.
- Run `./feurtube test` with JDK 21 and Android SDK build-tools 34.0.0. Tests exercise the released extension DEX and the actual Morphe loader. Passing them does not establish YouTube or Android compatibility.
- Upstream binaries are pinned in `upstream.lock.json`. Review source and update hashes deliberately. Never force an unsupported APK version through patching or continue after a failed patch.
- The combined desktop bundle retains RVX's `Patcher-Version: 1.7.0` behavior even though the pinned CLI exposes API 2.0.1. Changing the manifest to 2.x changes fingerprint matching and resource decoding for RVX too.
- Preserve upstream notices and visible credits. No proprietary APKs, signing keys, tokens, device identifiers, account screenshots or raw phone logs in Git or GitHub artifacts.
- Device tests use the separate package `app.feurtube.android`. Let the user handle authentication and account actions. Record only sanitized outcomes. Ask before interrupting personal playback or changing phone-wide settings.
- Keep docs factual and short. Label untested behavior. Do not add badges, release claims, broad feature patches or a website before the core app works.
