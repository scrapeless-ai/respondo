"""Release artifact checks use synthetic archives, never published packages."""

import io
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.verify_dist import REQUIRED_MODULES, REQUIRED_SOURCE_FILES, verify_dist


class DistributionTests(unittest.TestCase):
    VERSION = "0.6.0"

    def make_pair(self, root, *, wheel_extra=None, source_extra=None, metadata_extra="", omit=None):
        prefix = "respondo-0.6.0.dist-info/"
        metadata = ("Metadata-Version: 2.4\nName: respondo\nVersion: 0.6.0\n"
                    "Requires-Python: >=3.9\nLicense-Expression: MIT\n" + metadata_extra + "\nRespondo by Scrapeless\n")
        wheel_files = {name: b"# synthetic module\n" for name in REQUIRED_MODULES}
        wheel_files.update({prefix + "METADATA": metadata.encode(),
                            prefix + "WHEEL": b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
                            prefix + "RECORD": b"",
                            prefix + "entry_points.txt": b"[console_scripts]\nrespondo = respondo_cli:main\n",
                            prefix + "licenses/LICENSE": b"MIT License\n"})
        wheel_files.update(wheel_extra or {})
        if omit:
            wheel_files.pop(omit)
        with zipfile.ZipFile(root / "respondo-0.6.0-py3-none-any.whl", "w") as archive:
            for name, data in wheel_files.items():
                archive.writestr(name, data)
        source_files = {"respondo-0.6.0/" + name: b"synthetic\n" for name in REQUIRED_SOURCE_FILES}
        source_files.update({"respondo-0.6.0/src/" + name: b"# synthetic module\n" for name in REQUIRED_MODULES})
        source_files["respondo-0.6.0/PKG-INFO"] = metadata.encode()
        source_files.update(source_extra or {})
        with tarfile.open(root / "respondo-0.6.0.tar.gz", "w:gz") as archive:
            for name, data in source_files.items():
                member = tarfile.TarInfo(name)
                member.size = len(data)
                archive.addfile(member, io.BytesIO(data))

    def test_valid_pair_returns_both_checksums(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_pair(root)
            result = verify_dist(root, self.VERSION)
            self.assertEqual(set(result), {"respondo-0.6.0-py3-none-any.whl", "respondo-0.6.0.tar.gz"})
            self.assertTrue(all(len(value) == 64 for value in result.values()))

    def test_missing_distribution_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                verify_dist(Path(directory), self.VERSION)

    def test_console_entry_point_file_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_pair(Path(directory), omit="respondo-0.6.0.dist-info/entry_points.txt")
            with self.assertRaises(ValueError):
                verify_dist(Path(directory), self.VERSION)

    def test_duplicate_metadata_and_wrong_wheel_tag_fail(self):
        for extra, metadata in [({}, "Name: respondo\n"),
                                ({"respondo-0.6.0.dist-info/WHEEL": b"Root-Is-Purelib: true\nTag: cp312-linux\n"}, "")]:
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                self.make_pair(Path(directory), wheel_extra=extra, metadata_extra=metadata)
                with self.assertRaises(ValueError):
                    verify_dist(Path(directory), self.VERSION)

    def test_member_and_total_size_limits_fail_closed(self):
        for constant in ("MAX_MEMBER_BYTES", "MAX_ARCHIVE_BYTES"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as directory:
                self.make_pair(Path(directory))
                with patch("scripts.verify_dist." + constant, 1), self.assertRaises(ValueError):
                    verify_dist(Path(directory), self.VERSION)

    def test_duplicate_wheel_members_and_links_fail(self):
        for duplicate in (True, False):
            with self.subTest(duplicate=duplicate), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.make_pair(root)
                with zipfile.ZipFile(root / "respondo-0.6.0-py3-none-any.whl", "a") as archive:
                    if duplicate:
                        with self.assertWarns(UserWarning):
                            archive.writestr("respondo.py", b"duplicate")
                    else:
                        member = zipfile.ZipInfo("htmlparse/link")
                        member.create_system = 3
                        member.external_attr = (0o120777 << 16)
                        archive.writestr(member, b"outside")
                with self.assertRaises(ValueError):
                    verify_dist(root, self.VERSION)

    def test_missing_source_files_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_pair(root)
            with tarfile.open(root / "respondo-0.6.0.tar.gz", "w:gz"):
                pass
            with self.assertRaises(ValueError):
                verify_dist(root, self.VERSION)

    def test_missing_public_module_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_pair(Path(directory), omit="webparse/feeds.py")
            with self.assertRaises(ValueError):
                verify_dist(Path(directory), self.VERSION)

    def test_runtime_dependencies_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_pair(Path(directory), metadata_extra="Requires-Dist: unexpected-package\n")
            with self.assertRaises(ValueError):
                verify_dist(Path(directory), self.VERSION)

    def test_version_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            self.make_pair(Path(directory))
            with self.assertRaises(ValueError):
                verify_dist(Path(directory), "0.7.0")

    def test_unsafe_wheel_members_fail(self):
        for name in ("../outside", "/absolute", "a\\b", ".env", "webparse/__pycache__/x.pyc", "unexpected.py"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                self.make_pair(Path(directory), wheel_extra={name: b"synthetic"})
                with self.assertRaises(ValueError):
                    verify_dist(Path(directory), self.VERSION)

    def test_local_or_secret_source_files_fail(self):
        for name in ("respondo-0.6.0/.git/config", "respondo-0.6.0/.env", "respondo-0.6.0/key.pem",
                     "respondo-0.6.0/__pycache__/module.pyc", "other-root/README.md"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                self.make_pair(Path(directory), source_extra={name: b"synthetic"})
                with self.assertRaises(ValueError):
                    verify_dist(Path(directory), self.VERSION)

    def test_symlink_in_source_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_pair(root)
            with tarfile.open(root / "respondo-0.6.0.tar.gz", "w:gz") as archive:
                member = tarfile.TarInfo("respondo-0.6.0/link")
                member.type = tarfile.SYMTYPE
                member.linkname = "../../outside"
                archive.addfile(member)
            with self.assertRaises(ValueError):
                verify_dist(root, self.VERSION)


if __name__ == "__main__":
    unittest.main()
