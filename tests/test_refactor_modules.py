"""Unit tests for the refactored modules extracted from client.py."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"
if str(VISONIC_DIR) not in sys.path:
    sys.path.append(str(VISONIC_DIR))

import event_log  # noqa: E402
import registry_helper  # noqa: E402


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


class TestRegistryHelperModule(unittest.TestCase):
    """Tests for DeviceRegistry filtering and active identifier construction."""

    def test_filter_devices_matches_zones_x10_and_pgm_per_panel(self) -> None:
        """MED-07: Filter must include zones, X10 and PGM for the target panel only."""
        d_zone = SimpleNamespace(identifiers={("visonic", "visonic_z01")})
        d_x10 = SimpleNamespace(identifiers={("visonic", "visonic_x02")})
        d_pgm = SimpleNamespace(identifiers={("visonic", "visonic_pgm")})
        d_other_panel = SimpleNamespace(identifiers={("visonic", "visonic_p1_z01")})
        d_hub = SimpleNamespace(identifiers={("visonic", "Visonic Alarm")})

        matched = registry_helper.filter_devices_by_panel_prefix(
            [d_zone, d_x10, d_pgm, d_other_panel, d_hub],
            "visonic_",
        )
        self.assertEqual(matched, [d_zone, d_x10, d_pgm])

    def test_build_panel_device_identifiers_includes_raw_and_slugified_panel(self) -> None:
        """MED-07: Active identifier set includes raw and slugified panel name plus zones/switches."""
        sensor = SimpleNamespace(createFriendlyName=lambda: "Z01")
        switch = SimpleNamespace(createFriendlyName=lambda: "PGM")
        idents = registry_helper.build_panel_device_identifiers(
            panel_ident="Visonic Alarm",
            prefix="visonic_",
            sensor_list=[sensor],
            x10_list=[switch],
        )
        self.assertIn("Visonic Alarm", idents)
        self.assertIn("visonic_alarm", idents)
        self.assertIn("visonic_z01", idents)
        self.assertIn("visonic_pgm", idents)


class TestMarketplaceReadiness(unittest.TestCase):
    """Validate Home Assistant Marketplace / HACS manifest and brand assets."""

    def test_manifest_has_categories_and_valid_brand_assets(self) -> None:
        import json

        manifest = json.loads((VISONIC_DIR / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("categories", manifest)
        self.assertGreaterEqual(len(manifest["categories"]), 1)
        keys = list(manifest.keys())
        self.assertEqual(keys[:2], ["domain", "name"])
        self.assertEqual(keys[2:], sorted(keys[2:]))

        brand_dir = VISONIC_DIR / "brand"
        for filename in ("icon.png", "icon@2x.png", "logo.png", "logo@2x.png"):
            raw = (brand_dir / filename).read_bytes()
            self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n", f"{filename} is not a valid PNG")


if __name__ == "__main__":
    unittest.main()
