"""Report upstream releases without downloading or upgrading dependencies."""
import argparse
import base64
import html
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
MARKER = "<!-- feurtube-upstream-releases -->"
TITLE = "Upstream release review"
YOUTUBE_SOURCE = "patches/src/main/kotlin/app/morphe/patches/youtube/utils/compatibility/Constants.kt"


def api(method, path, payload=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "FeurTube-upstream-check"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request("https://api.github.com/" + path,
                                     data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def youtube_targets(source):
    source = re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.S)
    block = re.search(r"^([ \t]*)val\s+COMPATIBILITY_YOUTUBE\s*=\s*Compatibility\s*\((.*?)^\1\)",
                      source, flags=re.M | re.S)
    targets = re.search(r"\btargets\s*=\s*listOf\s*\((.*?)\)\s*,?\s*$", block[2], re.S) if block else None
    if not targets:
        raise ValueError("Unrecognized RVX YouTube compatibility declaration")
    entries = re.findall(r"\bAppTarget\s*\(([^()]*)\)", targets[1])
    remaining = re.sub(r"\bAppTarget\s*\([^()]*\)", "", targets[1])
    if not entries or remaining.strip(" \t\r\n,"):
        raise ValueError("Unrecognized RVX YouTube targets")
    versions = {False: [], True: []}
    field = r'\b(version|isExperimental|minSdk)\s*=\s*("[^"\n]*"|true|false|\d+)'
    seen = set()
    for entry in entries:
        pairs = re.findall(field, entry)
        values = dict(pairs)
        version = values.get("version", "").strip('"')
        experimental = values.get("isExperimental", "false")
        if (re.sub(field, "", entry).strip(" \t\r\n,") or len(pairs) != len(values)
                or not re.fullmatch(r'"\d+(?:\.\d+)+"', values.get("version", ""))
                or experimental not in ("true", "false") or version in seen
                or ("minSdk" in values and not values["minSdk"].isdigit())):
            raise ValueError("Unrecognized or duplicate RVX YouTube target")
        seen.add(version)
        versions[experimental == "true"].append(version)
    return {flag: sorted(items, key=lambda value: tuple(map(int, value.split('.'))), reverse=True)
            for flag, items in versions.items()}


def youtube_compatibility(tag, lock):
    ref = urllib.parse.quote(tag, safe="")
    result = api("GET", f"repos/anddea/revanced-patches/contents/{YOUTUBE_SOURCE}?ref={ref}")
    targets = youtube_targets(base64.b64decode(result["content"]).decode())
    allowed = {flag: sorted((version for version in lock["youtube"]["versions"]
                            if (version in lock["youtube"]["experimental"]) == flag),
                           key=lambda value: tuple(map(int, value.split('.'))), reverse=True)
               for flag in (False, True)}
    return [
        "| YouTube compatibility | Newest non-experimental target | Newest experimental target |",
        "| --- | --- | --- |",
        f"| FeurTube allowlist | {next(iter(allowed[False]), 'None')} | {next(iter(allowed[True]), 'None')} |",
        f"| Newest RVX publication | {next(iter(targets[False]), 'None')} | {next(iter(targets[True]), 'None')} |",
        "",
        f"[RVX compatibility source](https://github.com/anddea/revanced-patches/blob/{ref}/{YOUTUBE_SOURCE}). "
        "Upstream compatibility declarations do not establish FeurTube device compatibility.",
    ]


def snapshot(lock):
    rows = []
    compatibility = []
    for name, repository, pinned in (
        ("RVX patches", "anddea/revanced-patches", lock["patches"]["version"]),
        ("Morphe CLI", "MorpheApp/morphe-desktop", lock["cli"]["version"]),
        ("GmsCore", "ReVanced/GmsCore", None),
    ):
        releases = api("GET", f"repos/{repository}/releases?per_page=30")
        published = [release for release in releases if not release["draft"] and release["published_at"]]
        if not published:
            raise ValueError(f"No published releases found for {repository}")
        latest = max(published, key=lambda release: release["published_at"])
        tag = latest["tag_name"]
        url = f"https://github.com/{repository}/releases/tag/{urllib.parse.quote(tag, safe='')}"
        # Release names and notes are upstream content; only quote the tag as text.
        label = "<code>" + html.escape(tag).replace("|", "&#124;") + "</code>"
        rows.append(f"| {name} | {pinned or 'Installed separately'} | [{label}]({url}) |")
        if repository == "anddea/revanced-patches":
            compatibility = youtube_compatibility(tag, lock)
    return "\n".join([
        MARKER,
        "Review new upstream publications before changing FeurTube's pinned dependencies.",
        "A newer publication, including a prerelease or backport, does not establish compatibility.",
        "",
        "| Component | FeurTube pin | Newest publication |",
        "| --- | --- | --- |",
        *rows,
        "",
        *compatibility,
        "",
        "GmsCore is installed separately; compare its release with the version on the test device.",
        "Subscribe to this issue for changes. Unchanged checks do not post comments.",
        "Checks run weekly. GitHub may disable scheduled runs after 60 days of repository inactivity; "
        "the Upstream releases workflow can also be run manually from Actions.",
    ])


def notify(repository, body):
    page = 1
    while True:
        issues = api("GET", f"repos/{repository}/issues?state=all&per_page=100&page={page}")
        for issue in issues:
            if ("pull_request" not in issue and MARKER in (issue.get("body") or "")
                    and issue["user"]["login"] == "github-actions[bot]"):
                if issue["body"] != body:
                    # Post first so a failed issue edit cannot silently lose the notification.
                    api("POST", f"repos/{repository}/issues/{issue['number']}/comments", {"body": body})
                    api("PATCH", f"repos/{repository}/issues/{issue['number']}", {"body": body, "state": "open"})
                return issue["html_url"]
        if len(issues) < 100:
            break
        page += 1
    issue = api("POST", f"repos/{repository}/issues", {"title": TITLE, "body": body})
    return issue["html_url"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notify", action="store_true", help="create or update the GitHub tracking issue")
    args = parser.parse_args()
    body = snapshot(json.loads((ROOT / "upstream.lock.json").read_text()))
    print(notify(os.environ["GITHUB_REPOSITORY"], body) if args.notify else body)
