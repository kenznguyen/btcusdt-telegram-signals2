import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from ci.prepare_pinned_sqlite import (
    ARCHIVE_SHA3_256,
    SQLITE_SOURCE_ID,
    SQLITE_VERSION_NUMBER,
    verify_archive_digest,
    extract_and_pin,
)


class PinnedSqlitePreparationTests(unittest.TestCase):
    def make_archive(self, sqlite_c: bytes, sqlite_h: bytes) -> bytes:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("sqlite-amalgamation-3540100/sqlite3.c", sqlite_c)
            archive.writestr("sqlite-amalgamation-3540100/sqlite3.h", sqlite_h)
        return stream.getvalue()

    def test_archive_digest_is_sha3_256_and_fails_closed(self):
        payload = b"official release archive"
        expected = hashlib.sha3_256(payload).hexdigest()
        self.assertTrue(verify_archive_digest(payload, expected))
        with self.assertRaises(ValueError):
            verify_archive_digest(payload, "0" * 64)

    def test_extracts_only_expected_files_and_emits_exact_sha256_pins(self):
        sqlite_c = (
            f'#define SQLITE_SOURCE_ID "{SQLITE_SOURCE_ID}"\n'
            "int sqlite3_source_stub(void) { return 0; }\n"
        ).encode()
        sqlite_h = (
            f"#define SQLITE_VERSION_NUMBER {SQLITE_VERSION_NUMBER}\n"
            "#define SQLITE_VERSION \"3.54.1\"\n"
        ).encode()
        payload = self.make_archive(sqlite_c, sqlite_h)
        with tempfile.TemporaryDirectory() as tmp:
            vendor = Path(tmp) / "vendor"
            pin_file = Path(tmp) / "generated" / "sqlite3-pins.cmake"
            extract_and_pin(payload, vendor, pin_file)
            self.assertEqual((vendor / "sqlite3.c").read_bytes(), sqlite_c)
            self.assertEqual((vendor / "sqlite3.h").read_bytes(), sqlite_h)
            pins = pin_file.read_text()
            self.assertIn(f'SQLITE_EXPECTED_VERSION_NUMBER "{SQLITE_VERSION_NUMBER}"', pins)
            self.assertIn(f'SQLITE_EXPECTED_SOURCE_ID "{SQLITE_SOURCE_ID}"', pins)
            self.assertIn(hashlib.sha256(sqlite_c).hexdigest(), pins)
            self.assertIn(hashlib.sha256(sqlite_h).hexdigest(), pins)

    def test_rejects_wrong_sqlite_version_or_source_id(self):
        sqlite_c = b'#define SQLITE_SOURCE_ID "wrong-source-id"\n'
        sqlite_h = b"#define SQLITE_VERSION_NUMBER 3037000\n"
        payload = self.make_archive(sqlite_c, sqlite_h)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                extract_and_pin(payload, Path(tmp) / "vendor", Path(tmp) / "pins.cmake")

    def test_rejects_archive_missing_amalgamation_members(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("unexpected.txt", "not sqlite")
        payload = stream.getvalue()
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                extract_and_pin(payload, Path(tmp) / "vendor", Path(tmp) / "pins.cmake")


if __name__ == "__main__":
    unittest.main()
