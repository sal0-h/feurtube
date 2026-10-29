# Upstream provenance

| Project | Revision inspected / used | Role |
| --- | --- | --- |
| [FeurStagram](https://github.com/jean-voila/FeurStagram/tree/d09d7fd371d96084c852965c414587a8b1a8b372) | `d09d7fd371d96084c852965c414587a8b1a8b372` | Architecture reference; no Instagram code copied |
| [anddea/RVX](https://github.com/anddea/revanced-patches/tree/3de8b752ce00501cd847c0eacf463dd58cb97ed4) | `v4.4.0-dev.3`, `3de8b752ce00501cd847c0eacf463dd58cb97ed4` | Bytecode fingerprints, filtering, navigation, settings, account integration |
| [Morphe Desktop](https://github.com/MorpheApp/morphe-desktop/tree/10283481b8497172e07c28c170e46618ef648ae1) | `v1.19.1` | APK patching engine and JVM API |

FeurTube downloads the original RVX bundle, verifies its release SHA-256 and adds a separate policy. The generated bundle preserves upstream JVM classes and applies one resource overlay to replace a misleading Shorts player selector with a fixed explanation. When applied, our patch modifies the injected `Setting` constructor and replaces `ShortsPatch.openShortInRegularPlayer`. The redirect follows the upstream route with different handling for empty launches and the selected Shorts tab. These modifications are FeurTube's, not an upstream release.

Credit belongs to anddea (Aaron Veil), inotia00, the Morphe contributors and the contributors credited in the pinned source. Existing upstream in-app About/credits remain. The complete upstream NOTICE is retained at the repository root and in the generated bundle. Upstream source headers and history remain available at the pinned source revision. Additional attribution terms appear in that source and in NOTICE.

The release digests pin the files we use. They do not establish that an upstream binary was built from its published source. To rebuild RVX, use its pinned source and build instructions; its Gradle plugin/dependencies require access to Morphe's GitHub Packages registry. We attempted that build here, but plugin resolution failed. FeurTube's own policy build does not need registry credentials.

The input APK certificate allowlist contains the legacy `24bb…` YouTube signer and its rotated signer. Their full SHA-256 fingerprints were verified with Android SDK `apksigner` against the installed Google Play YouTube APK on the test phone. The old SHA-1 identity also matches RVX's pinned `GmsCoreSupportPatch.kt`. Other legitimate signing variants may be rejected until reviewed.

FeurStagram's `NetworkBlockPatch.kt`, `FeedItemFilterPatch.kt`, `Hiders.java` and `LimitFeedToFollowingPatch.kt` demonstrate network, parser and view hooks. Those Instagram endpoints and fingerprints do not apply to YouTube. YouTube's Shorts surfaces share services with normal playback, so this implementation starts at rendering and navigation rather than blocking broad video endpoints.
