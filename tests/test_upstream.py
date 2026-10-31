import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("upstream", Path(__file__).resolve().parents[1] / ".github/scripts/upstream.py")
upstream = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upstream)


class UpstreamTests(unittest.TestCase):
    def test_snapshot_uses_publication_dates_and_excludes_drafts(self):
        releases = [
            {"tag_name": "v2", "published_at": "2026-10-10T00:00:00Z", "draft": False},
            {"tag_name": "v3", "published_at": None, "draft": True},
            {"tag_name": "v1.1-beta.1", "published_at": "2026-10-20T00:00:00Z", "draft": False},
        ]
        with patch.object(upstream, "api", return_value=releases) as api:
            body = upstream.snapshot({"patches": {"version": "1.0"}, "cli": {"version": "1.2"}})
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
