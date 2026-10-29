# Repository rules

- Keep README concise. The public setup guide lives in `site/`; keep its compatibility facts consistent with README. Do not add handoffs, session journals or status reports.
- Comments should explain non-obvious constraints, not narrate the code. Preserve license and attribution comments.
- Run `./feurtube test` with JDK 21 and Android SDK build-tools 34.0.0. Host tests do not establish Android compatibility.
- Keep dependencies pinned in `upstream.lock.json`. Preserve LICENSE, NOTICE and upstream credits. Do not commit APKs, keys, credentials or phone captures.
- Device tests target `app.feurtube.android`. Leave other apps, data and security settings alone. The user handles authentication. Ask before interrupting playback or changing phone-wide settings; never capture login forms or other apps.
