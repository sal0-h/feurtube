import base64
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("upstream", Path(__file__).resolve().parents[1] / ".github/scripts/upstream.py")
upstream = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upstream)

COMPATIBILITY = '''
internal object Constants {
    val COMPATIBILITY_YOUTUBE = Compatibility(
        name = "YouTube",
        packageName = YOUTUBE_PACKAGE_NAME,
        targets = listOf(
            AppTarget(version = "21.39.525", isExperimental = true, minSdk = 32),
            AppTarget(version = "21.9.100", minSdk = 28),
            AppTarget(minSdk = 28, version = "21.13.164", isExperimental = false),
        )
    )
    val OTHER_VERSIONS = listOf("99.99.999")
}
'''


class UpstreamTests(unittest.TestCase):
    def test_youtube_targets_sort_numerically_and_keep_experimental_separate(self):
        self.assertEqual(upstream.youtube_targets(COMPATIBILITY),
                         {False: ["21.13.164", "21.9.100"], True: ["21.39.525"]})

    def test_unrecognized_compatibility_fails_instead_of_claiming_no_new_targets(self):
        for source in ("", COMPATIBILITY.replace("AppTarget", "NewTarget"),
                       COMPATIBILITY.replace('"21.39.525"', '"21.39.525-beta"'),
                       COMPATIBILITY.replace("isExperimental = true", "isExperimental = experimentalFlag"),
                       COMPATIBILITY.replace("21.9.100", "21.13.164")):
            with self.subTest(source=source), self.assertRaises(ValueError):
                upstream.youtube_targets(source)

    def test_compatibility_is_read_from_the_selected_release_tag(self):
        source = {"content": base64.b64encode(COMPATIBILITY.encode()).decode()}
        lock = {"youtube": {"versions": ["21.13.164", "21.39.525"], "experimental": ["21.39.525"]}}
        with patch.object(upstream, "api", return_value=source) as api:
            before = upstream.youtube_compatibility("v4.4.0-dev.6", lock)
        self.assertTrue(api.call_args.args[1].endswith("?ref=v4.4.0-dev.6"))
        with patch.object(upstream, "api", return_value={"content": base64.b64encode(
                COMPATIBILITY.replace("21.39.525", "21.43.525").encode()).decode()}):
            after = upstream.youtube_compatibility("v4.4.0-dev.6", lock)
        self.assertNotEqual(before, after)
        self.assertIn("| FeurTube allowlist | 21.13.164 | 21.39.525 |", after)
        self.assertIn("| Newest RVX publication | 21.13.164 | 21.43.525 |", after)

    def test_snapshot_uses_publication_dates_and_excludes_drafts(self):
        releases = [
            {"tag_name": "v2", "published_at": "2026-10-10T00:00:00Z", "draft": False},
            {"tag_name": "v3", "published_at": None, "draft": True},
            {"tag_name": "v1.1-beta.1", "published_at": "2026-10-20T00:00:00Z", "draft": False},
        ]
        with (patch.object(upstream, "api", return_value=releases) as api,
              patch.object(upstream, "youtube_compatibility", return_value=[]) as compatibility):
            body = upstream.snapshot({"patches": {"version": "1.0"}, "cli": {"version": "1.2"}})
        self.assertEqual(compatibility.call_args.args[0], "v1.1-beta.1")
        self.assertEqual(body.count("<code>v1.1-beta.1</code>"), 3)
        self.assertNotIn("<code>v3</code>", body)
        self.assertTrue(all(call.args[0] == "GET" for call in api.call_args_list))

    def test_missing_release_fails_instead_of_posting_incomplete_snapshot(self):
        with patch.object(upstream, "api", return_value=[]):
            with self.assertRaisesRegex(ValueError, "No published releases"):
                upstream.snapshot({"patches": {"version": "1.0"}, "cli": {"version": "1.2"}})

    def issue(self, body):
        return {"number": 7, "body": body, "user": {"login": "github-actions[bot]"}, "html_url": "https://github.com/test/repo/issues/7"}

    def test_unchanged_snapshot_does_not_notify(self):
        body = upstream.MARKER + "same releases"
        with patch.object(upstream, "api", return_value=[self.issue(body)]) as api:
            upstream.notify("test/repo", body)
        self.assertEqual(api.call_count, 1)

    def test_changed_snapshot_comments_then_updates_same_issue(self):
        body = upstream.MARKER + "new releases"
        with patch.object(upstream, "api", side_effect=[[self.issue(upstream.MARKER + "old")], {}, {}]) as api:
            upstream.notify("test/repo", body)
        self.assertEqual([call.args[0] for call in api.call_args_list], ["GET", "POST", "PATCH"])
        self.assertEqual(api.call_args_list[1].args[1], "repos/test/repo/issues/7/comments")
        self.assertEqual(api.call_args_list[2].args[2], {"body": body, "state": "open"})

    def test_human_issue_cannot_impersonate_automation(self):
        human = self.issue(upstream.MARKER)
        human["user"]["login"] = "someone"
        with patch.object(upstream, "api", side_effect=[[human], self.issue("new")]) as api:
            upstream.notify("test/repo", "new")
        self.assertEqual(api.call_args.args[1], "repos/test/repo/issues")

    def test_failed_notification_leaves_previous_state_for_retry(self):
        with patch.object(upstream, "api", side_effect=[[self.issue(upstream.MARKER)], OSError("offline")]) as api:
            with self.assertRaises(OSError):
                upstream.notify("test/repo", upstream.MARKER + "new")
        self.assertEqual(api.call_count, 2)


if __name__ == "__main__":
    unittest.main()
