"""Unit tests for the refactored modules extracted from client.py."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"
if str(VISONIC_DIR) not in sys.path:
    sys.path.append(str(VISONIC_DIR))

import event_log  # noqa: E402


class TestEventLogModule(unittest.TestCase):
    """Tests for event_log path validation and CSV writing."""

    def test_resolve_allowed_log_path_blocks_traversal(self) -> None:
        """MED-05: Paths escaping the Home Assistant config directory must be rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            allowed = event_log.resolve_allowed_log_path(tmpdir, "visonic_log.csv")
            self.assertIsNotNone(allowed)
            self.assertTrue(Path(allowed).is_relative_to(Path(tmpdir).resolve()))

            blocked_rel = event_log.resolve_allowed_log_path(tmpdir, "../outside.csv")
            self.assertIsNone(blocked_rel)

            blocked_abs = event_log.resolve_allowed_log_path(tmpdir, str(Path(tmpdir).parent / "evil.csv"))
            self.assertIsNone(blocked_abs)

    def test_write_panel_event_log_files_writes_csv_with_header(self) -> None:
        """CSV writer outputs UTF-8 content with optional title header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = event_log.resolve_allowed_log_path(tmpdir, "events.csv")
            self.assertIsNotNone(csv_path)
            errors = event_log.write_panel_event_log_files(
                available=1,
                total=1,
                templatedata=None,
                csvdata="1, 1, 1, 2026-11-27, 10:00, Zone 01, Armed\n",
                xml_path=None,
                csv_path=csv_path,
                config_path=tmpdir,
                template_filename="visonic_template.xml",
                add_csv_title=True,
            )
            self.assertEqual(errors, [])
            content = Path(csv_path).read_text(encoding="utf-8")
            self.assertTrue(content.startswith("current, total, partition, date, time, zone, event\n"))
            self.assertIn("Zone 01, Armed", content)


if __name__ == "__main__":
    unittest.main()
