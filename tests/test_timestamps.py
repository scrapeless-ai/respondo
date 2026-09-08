"""UTC timestamps must not depend on the machine's local time zone."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cryptoutil import from_timestamp, to_timestamp


class TimestampTests(unittest.TestCase):
    def test_explicit_utc_never_uses_local_conversion(self):
        with patch("cryptoutil.time.mktime", return_value=42) as local:
            self.assertEqual(to_timestamp("2024-01-15T12:00:00Z"), 1705320000)
            self.assertEqual(to_timestamp("1970-01-01T00:00:00Z"), 0)
            local.assert_not_called()
        self.assertEqual(from_timestamp(1705320000), "2024-01-15T12:00:00Z")

    def test_unzoned_input_retains_legacy_local_time_semantics(self):
        for value in ("2024-01-15T12:00:00", "2024-01-15 12:00:00", "2024-01-15"):
            with self.subTest(value=value), patch("cryptoutil.time.mktime", return_value=42) as local:
                self.assertEqual(to_timestamp(value), 42)
                local.assert_called_once()

    def test_invalid_dates_retain_zero_result(self):
        for value in ("", "not a date", "2024-02-30T12:00:00Z"):
            with self.subTest(value=value):
                self.assertEqual(to_timestamp(value), 0)


if __name__ == "__main__":
    unittest.main()
