import importlib.machinery
import importlib.util
import os
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import zipfile
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader("feurtube", str(Path(__file__).resolve().parents[1] / "feurtube"))
spec = importlib.util.spec_from_loader(loader.name, loader)
ft = importlib.util.module_from_spec(spec)
loader.exec_module(ft)


class BuildTests(unittest.TestCase):
    def test_actual_report_format_lists_selected_roots(self):
        report = json.loads((ft.ROOT / "tests/fixtures/patch-report.json").read_text())
        ft.validate_report(report)
        report["failedPatches"] = [{"name": "FeurTube policy", "error": "test"}]
        with self.assertRaises(ValueError):
            ft.validate_report(report)

    def test_report_with_failed_rebuild_is_rejected(self):
        report = json.loads((ft.ROOT / "tests/fixtures/patch-report.json").read_text())
        report["stepResults"][-1]["success"] = False
        with self.assertRaises(ValueError):
            ft.validate_report(report)

    def test_patch_selection(self):
        with patch.dict(os.environ, {"JAVA_HOME": "/usr"}):
            args = list(map(str, ft.patch_arguments("cli", "upstream", "policy", "in.apk", "out.apk", "report", "scratch")))
        enabled = [args[i + 1] for i, value in enumerate(args) if value == "-e"]
        self.assertIn("--exclusive", args)
        self.assertNotIn("-f", args)
        self.assertNotIn("--continue-on-error", args)
        self.assertIn("FeurTube policy", enabled)
        self.assertIn("Hide shortcuts", enabled)
        self.assertNotIn("Spoof app version", enabled)
        self.assertIn("packageNameYouTube=app.feurtube.android", args)
        self.assertIn("rvxSettingsLabel=FeurTube", args)

    def test_wrong_package_and_version_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "input.apk"
            apk.touch()
            for metadata in [("other.app", "21.13.164"), ("com.google.android.youtube", "1.0")]:
                with patch.object(ft, "apk_metadata", return_value=metadata):
                    with self.assertRaisesRegex(ValueError, "Unsupported input"):
                        ft.validate_input(apk)

    def test_corrupt_cached_dependency_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ft, "CACHE", Path(directory)):
            first = ft.LOCK["cli"]["url"].rsplit("/", 1)[1]
            (Path(directory) / first).write_bytes(b"wrong artifact")
            with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
                ft.bootstrap()

    def test_deterministic_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = [Path(directory) / name for name in ("a.zip", "b.zip")]
            ft.archive(a, {"b": b"two", "a": b"one"})
            ft.archive(b, {"a": b"one", "b": b"two"})
            self.assertEqual(ft.digest(a), ft.digest(b))

    def test_reject_unknown_signer(self):
        output = "Signer #1 certificate SHA-256 digest: " + "0" * 64 + "\n"
        with patch.object(ft, "sdk_tool", return_value="apksigner"), patch.object(ft, "run", return_value=SimpleNamespace(stdout=output)):
            with self.assertRaisesRegex(ValueError, "signing certificate"):
                ft.verify_input_signature(Path("fake.apk"))

    def test_accept_pinned_signer(self):
        certificate = ft.LOCK["youtube"]["certificate_sha256"][0]
        output = f"Signer #1 certificate SHA-256 digest: {certificate}\n"
        with patch.object(ft, "sdk_tool", return_value="apksigner"), patch.object(ft, "run", return_value=SimpleNamespace(stdout=output)):
            self.assertEqual(ft.verify_input_signature(Path("fake.apk")), [certificate])

    def test_policy_preference_replaces_misleading_player_selector(self):
        path = "youtube/settings/xml/revanced_prefs.xml"
        upstream = ft.CACHE / ft.LOCK["patches"]["url"].rsplit("/", 1)[1]
        with zipfile.ZipFile(upstream) as source:
            entries = {path: source.read(path)}
        ft.configure_resources(entries)
        self.assertIn(b'android:key="feurtube_shorts_policy"', entries[path])
        self.assertNotIn(b'android:key="revanced_shorts_player_type"', entries[path])
        with self.assertRaisesRegex(ValueError, "Expected one upstream"):
            ft.configure_resources(entries)


if __name__ == "__main__":
    unittest.main()
