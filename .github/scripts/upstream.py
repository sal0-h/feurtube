"""Report upstream releases without downloading or upgrading dependencies."""
import argparse
import html
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
MARKER = "<!-- feurtube-upstream-releases -->"
TITLE = "Upstream release review"


def api(method, path, payload=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "FeurTube-upstream-check"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request("https://api.github.com/" + path,
                                     data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def snapshot(lock):
    rows = []
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
    return "\n".join([
        MARKER,
        "Review new upstream publications before changing FeurTube's pinned dependencies.",
        "A newer publication, including a prerelease or backport, does not establish compatibility.",
        "",
        "| Component | FeurTube pin | Newest publication |",
        "| --- | --- | --- |",
        *rows,
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
