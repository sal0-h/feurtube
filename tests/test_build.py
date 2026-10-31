import importlib.machinery
import importlib.util
import os
import json
from pathlib import Path
import tempfile
import subprocess
from types import SimpleNamespace
import unittest
import zipfile
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader("feurtube", str(Path(__file__).resolve().parents[1] / "feurtube"))
spec = importlib.util.spec_from_loader(loader.name, loader)
ft = importlib.util.module_from_spec(spec)
loader.exec_module(ft)


class BuildTests(unittest.TestCase):
    def test_wrong_jdk_rejected_before_sdk_checks(self):
        result = SimpleNamespace(stdout="", stderr='openjdk version "27.0.1"')
        with (patch.object(ft, "java_tool", return_value="java"),
              patch.object(ft, "run", return_value=result),
              patch.object(ft, "sdk_tool") as sdk):
            with self.assertRaisesRegex(ValueError, "JDK 21 required"):
                ft.check_environment()
            sdk.assert_not_called()

    def test_mismatched_compiler_rejected(self):
        results = [SimpleNamespace(stdout="", stderr='openjdk version "21.0.9"'),
                   SimpleNamespace(stdout="javac 27.0.1", stderr="")]
        with (patch.object(ft, "java_tool", side_effect=lambda name: name),
              patch.object(ft, "run", side_effect=results)):
            with self.assertRaisesRegex(ValueError, "javac reports 27"):
                ft.check_environment()

    def test_noninteractive_password_is_not_read_or_echoed(self):
        with (patch.dict(os.environ, {}, clear=True),
              patch.object(ft.sys.stdin, "isatty", return_value=False),
              patch.object(ft.getpass, "getpass") as prompt):
            with self.assertRaisesRegex(ValueError, "run in a terminal"):
                ft.ensure_password()
            prompt.assert_not_called()

    def test_password_confirmation_failure_does_not_set_password(self):
        with (patch.dict(os.environ, {}, clear=True),
              patch.object(ft.sys.stdin, "isatty", return_value=True),
              patch.object(ft.getpass, "getpass", side_effect=["test-secret", "different"])):
            with self.assertRaisesRegex(ValueError, "did not match"):
                ft.ensure_password(confirm=True)
            self.assertNotIn("FEURTUBE_KEYSTORE_PASSWORD", os.environ)

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


class KeystoreTests(unittest.TestCase):
    def test_keygen_creates_private_key_and_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / "private/key.p12"
            with patch.dict(os.environ, {"FEURTUBE_KEYSTORE_PASSWORD": "test-only-password"}):
                ft.keygen(SimpleNamespace(keystore=key))
            self.assertTrue(key.is_file())
            self.assertEqual(key.stat().st_mode & 0o777, 0o600)
            self.assertEqual(key.parent.stat().st_mode & 0o777, 0o700)
            original = ft.digest(key)
            with self.assertRaisesRegex(ValueError, "Refusing to replace"):
                ft.keygen(SimpleNamespace(keystore=key))
            self.assertEqual(ft.digest(key), original)

    def test_new_key_uses_platform_data_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (patch.object(ft.Path, "home", return_value=root),
                  patch.object(ft, "CACHE", root / "cache"),
                  patch.dict(os.environ, {"XDG_DATA_HOME": "relative-path"})):
                for platform, expected in (("linux", ".local/share"), ("darwin", "Library/Application Support")):
                    with patch.object(ft.sys, "platform", platform):
                        self.assertEqual(ft.default_keystore(), root / expected / "feurtube/signing.p12")

    def test_legacy_key_is_used_until_identical_copy_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache, data = root / "cache", root / "data"
            cache.mkdir()
            legacy = cache / "signing.p12"
            legacy.write_bytes(b"existing test key")
            key = data / "feurtube/signing.p12"
            with (patch.object(ft, "CACHE", cache), patch.object(ft.sys, "platform", "linux"),
                  patch.dict(os.environ, {"XDG_DATA_HOME": str(data)})):
                self.assertEqual(ft.default_keystore(), legacy)
                key.parent.mkdir(parents=True)
                key.write_bytes(legacy.read_bytes())
                self.assertEqual(ft.default_keystore(), key)
                key.write_bytes(b"different test key")
                with self.assertRaisesRegex(ValueError, "select one with --keystore"):
                    ft.default_keystore()
                self.assertEqual(legacy.read_bytes(), b"existing test key")

    def test_explicit_key_bypasses_default_selection(self):
        with (patch.object(ft.sys, "argv", ["feurtube", "keygen", "--keystore", "/tmp/test-key.p12"]),
              patch.object(ft, "default_keystore") as default,
              patch.object(ft, "keygen") as keygen):
            self.assertEqual(ft.main(), 0)
            default.assert_not_called()
            self.assertEqual(keygen.call_args.args[0].keystore, Path("/tmp/test-key.p12"))

    def test_keygen_does_not_follow_a_broken_key_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / "key.p12"
            target = Path(directory) / "missing.p12"
            key.symlink_to(target)
            with patch.object(ft, "ensure_password") as password:
                with self.assertRaisesRegex(ValueError, "Refusing to replace"):
                    ft.keygen(SimpleNamespace(keystore=key))
                password.assert_not_called()
            self.assertFalse(target.exists())


class OutputTests(unittest.TestCase):
    def test_receipt_cannot_replace_the_apk_or_keystore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "end in .apk"):
                ft.validate_output(root / "app.json", root / "input.apk", root / "key.p12")
            key = root / "app.json"
            key.write_bytes(b"private key")
            with self.assertRaisesRegex(ValueError, "new paths"):
                ft.validate_output(root / "app.apk", root / "input.apk", key)
            self.assertEqual(key.read_bytes(), b"private key")

    def test_broken_output_symlink_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output.apk"
            destination = root / "future.apk"
            output.symlink_to(destination)
            with self.assertRaisesRegex(ValueError, "new paths"):
                ft.validate_output(output, root / "input.apk", root / "key.p12")
            self.assertTrue(output.is_symlink())
            self.assertFalse(destination.exists())

    def test_receipt_created_during_patching_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            signed, output = root / "signed.apk", root / "output.apk"
            signed.write_bytes(b"signed apk")
            output.with_suffix(".json").write_text("existing data")
            with self.assertRaises(FileExistsError):
                ft.publish_outputs(signed, output, {})
            self.assertFalse(output.exists())
            self.assertEqual(output.with_suffix(".json").read_text(), "existing data")

    def test_interrupted_copy_removes_incomplete_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            signed, output = root / "signed.apk", root / "output.apk"
            signed.write_bytes(b"signed apk")
            with patch.object(ft.shutil, "copyfileobj", side_effect=OSError("disk full")):
                with self.assertRaisesRegex(OSError, "disk full"):
                    ft.publish_outputs(signed, output, {})
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".json").exists())

    def test_failed_signature_verification_does_not_publish_an_apk(self):
        report = (ft.ROOT / "tests/fixtures/patch-report.json").read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apk, key, output = root / "input.apk", root / "key.p12", root / "output.apk"
            apk.write_bytes(b"input apk")
            key.write_bytes(b"private key")
            args = SimpleNamespace(apk=apk, keystore=key, output=output, experimental=False)

            def run(command, **kwargs):
                if "-r" in command:
                    Path(command[command.index("-r") + 1]).write_text(report)
                elif "sign" in command:
                    Path(command[command.index("--out") + 1]).write_bytes(b"bad signature")
                elif "verify" in command:
                    raise subprocess.CalledProcessError(1, command)

            with (patch.object(ft, "BUILD", root),
                  patch.object(ft, "validate_input", return_value="21.13.164"),
                  patch.object(ft, "verify_input_signature", return_value=[]),
                  patch.object(ft, "ensure_password"),
                  patch.object(ft, "build", return_value=(root / "cli", root / "upstream", root / "bundle")),
                  patch.object(ft, "apk_metadata", return_value=(ft.PACKAGE, "21.13.164")),
                  patch.object(ft, "java_tool", return_value="java"),
                  patch.object(ft, "sdk_tool", side_effect=lambda name: name),
                  patch.object(ft, "run", side_effect=run)):
                with self.assertRaises(subprocess.CalledProcessError):
                    ft.patch(args)
            self.assertFalse(output.exists())
            self.assertFalse(output.with_suffix(".json").exists())
            self.assertEqual(apk.read_bytes(), b"input apk")
            self.assertEqual(key.read_bytes(), b"private key")


if __name__ == "__main__":
    unittest.main()
