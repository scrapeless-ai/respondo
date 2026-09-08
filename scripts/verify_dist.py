"""Inspect release archives without extracting or executing their contents."""

import argparse
from email.parser import BytesParser
import hashlib
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import zipfile


REQUIRED_MODULES = {
    "respondo.py", "respondo_cli.py", "respondo_batch.py", "_respondo_version.py",
    "textparse/__init__.py", "jsonparse/__init__.py", "jsonparse/records.py",
    "htmlparse/__init__.py", "htmlparse/page.py", "htmlparse/selectors.py",
    "responseutil/__init__.py", "responseutil/headers.py", "cryptoutil/__init__.py",
    "ai/__init__.py", "webparse/__init__.py", "webparse/urls.py", "webparse/feeds.py",
    "botprotection/__init__.py", "botprotection/detect.py",
    *("botprotection/" + name + "/__init__.py" for name in
      ("akamai", "datadome", "hcaptcha", "incapsula", "kasada", "recaptcha", "turnstile")),
}
REQUIRED_SOURCE_FILES = {
    "LICENSE", "README.md", "README.pypi.md", "pyproject.toml", "MANIFEST.in",
    "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "RELEASING.md",
    "requirements-release.in", "requirements-release.txt", ".coveragerc",
    "docs/API.md", "docs/SCRAPELESS.md", "scripts/run_tests.py", "scripts/verify_dist.py",
    "scripts/smoke_installed.py", "tests/test_distribution.py",
    "examples/extraction_pipeline.py", "examples/cards.html", "examples/card-fields.json",
    "examples/feed.xml", "examples/sitemap.xml", "assets/scrapeless-logo.svg",
    "assets/respondo-scrapeless-banner.png", "assets/README.md",
}
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024


def _safe_name(name):
    parts = name.rstrip("/").split("/")
    if not name or "\\" in name or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("unsafe archive member path")
    if any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise ValueError("control character in archive member path")
    lower = [part.lower() for part in parts]
    forbidden = {".git", ".claude", ".codex", ".venv", "node_modules", "__pycache__", "agents.md", "claude.md"}
    if forbidden.intersection(lower) or any(part == ".env" or part.startswith(".env.") for part in lower):
        raise ValueError("machine-local or secret-bearing file in archive")
    if PurePosixPath(name).suffix.lower() in {".pyc", ".pyo", ".pem", ".key", ".p12", ".pfx"}:
        raise ValueError("compiled or credential file in archive")


def _members(path):
    files = {}
    seen = set()
    total = 0

    def check(name, size):
        nonlocal total
        _safe_name(name)
        if name in seen:
            raise ValueError("duplicate archive member")
        seen.add(name)
        total += size
        if size < 0 or size > MAX_MEMBER_BYTES or total > MAX_ARCHIVE_BYTES:
            raise ValueError("release archive exceeds size limit")

    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                check(member.filename, member.file_size)
                if stat.S_ISLNK(member.external_attr >> 16):
                    raise ValueError("archive links are not allowed")
                if not member.is_dir():
                    files[member.filename] = archive.read(member)
    else:
        with tarfile.open(path, "r:gz") as archive:
            for member in archive:
                check(member.name, member.size)
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ValueError("archive links and special files are not allowed")
                with archive.extractfile(member) as stream:
                    files[member.name] = stream.read()
    return files


def _metadata(data, version):
    metadata = BytesParser().parsebytes(data)
    for key, expected in {"Name": "respondo", "Version": version, "Requires-Python": ">=3.9", "License-Expression": "MIT"}.items():
        if metadata.get_all(key) != [expected]:
            raise ValueError("incorrect or duplicate package metadata: " + key)
    if metadata.get_all("Requires-Dist"):
        raise ValueError("runtime dependencies are not allowed")


def verify_dist(directory, expected_version):
    """Return SHA-256 values only after both distribution formats pass checks."""
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", expected_version):
        raise ValueError("expected a final three-part release version")
    directory = Path(directory)
    wheel = directory / ("respondo-" + expected_version + "-py3-none-any.whl")
    source = directory / ("respondo-" + expected_version + ".tar.gz")
    if set(directory.glob("*.whl")) != {wheel} or set(directory.glob("*.tar.gz")) != {source}:
        raise ValueError("expected exactly one matching wheel and one matching source distribution")
    wheel_files = _members(wheel)
    prefix = "respondo-" + expected_version + ".dist-info/"
    metadata_files = {prefix + name for name in ("METADATA", "WHEEL", "RECORD", "entry_points.txt", "top_level.txt", "licenses/LICENSE")}
    if not REQUIRED_MODULES.issubset(wheel_files):
        raise ValueError("wheel is missing a public module")
    if set(wheel_files) - REQUIRED_MODULES - metadata_files:
        raise ValueError("unexpected file in wheel")
    for required in ("METADATA", "WHEEL", "RECORD", "entry_points.txt", "licenses/LICENSE"):
        if prefix + required not in wheel_files:
            raise ValueError("missing wheel metadata or license")
    _metadata(wheel_files[prefix + "METADATA"], expected_version)
    wheel_metadata = BytesParser().parsebytes(wheel_files[prefix + "WHEEL"])
    if wheel_metadata.get("Root-Is-Purelib") != "true" or wheel_metadata.get_all("Tag") != ["py3-none-any"]:
        raise ValueError("wheel is not platform-independent pure Python")
    source_files = _members(source)
    source_prefix = "respondo-" + expected_version + "/"
    if any(not name.startswith(source_prefix) for name in source_files):
        raise ValueError("unexpected source archive root")
    expected = REQUIRED_SOURCE_FILES | {"src/" + name for name in REQUIRED_MODULES} | {"PKG-INFO"}
    if not {source_prefix + name for name in expected}.issubset(source_files):
        raise ValueError("source distribution is missing release files")
    _metadata(source_files[source_prefix + "PKG-INFO"], expected_version)
    result = {}
    for path in (wheel, source):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        result[path.name] = digest.hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        checksums = verify_dist(args.directory, args.version)
    except (ValueError, OSError, zipfile.BadZipFile, tarfile.TarError):
        parser.exit(1, "release verification failed; inspect archive contents and metadata locally\n")
    for name, checksum in checksums.items():
        print(checksum + "  " + name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
