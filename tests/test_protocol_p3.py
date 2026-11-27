"""Regression tests for P3 fixes (PIN edge cases, image buffer bounds, memory cap)."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"
if str(VISONIC_DIR) not in sys.path:
    sys.path.append(str(VISONIC_DIR))

from protocol import enums as pyenum  # noqa: E402
from protocol import helper as pyhelper  # noqa: E402
from protocol import visonic as pyvisonic  # noqa: E402


class TestProtocolP3(unittest.TestCase):
    """P3 regression tests for protocol edge cases and bounded image storage."""

    def test_is_valid_user_code_accepts_zero_prefixed_and_suffixed_pins(self) -> None:
        """MED-09: Valid PINs like 0012 or 1200 must be accepted; 0000 must be rejected."""
        proto = object.__new__(pyvisonic.VisonicProtocol)
        proto.ForceStandardMode = False

        proto.PanelSettings = {pyenum.PanelSetting.UserCodes: bytearray([0x00, 0x12])}
        self.assertTrue(proto._is_valid_user_code())

        proto.PanelSettings = {pyenum.PanelSetting.UserCodes: bytearray([0x12, 0x00])}
        self.assertTrue(proto._is_valid_user_code())

        proto.PanelSettings = {pyenum.PanelSetting.UserCodes: bytearray([0x00, 0x00])}
        self.assertFalse(proto._is_valid_user_code())

    def test_create_pin_handles_non_numeric_input_safely(self) -> None:
        """MED-09: _createPin must not raise ValueError on non-hex 4-char strings."""
        proto = object.__new__(pyvisonic.VisonicProtocol)
        self.assertEqual(proto._createPin("1234"), bytearray([0x12, 0x34]))
        self.assertEqual(proto._createPin("test"), bytearray([0x00, 0x00]))
        self.assertEqual(proto._createPin("12z4"), bytearray([0x00, 0x00]))

    def test_image_record_rejects_buffer_overflow(self) -> None:
        """MED-10: ImageRecord.addBufferData must reject chunks exceeding declared size."""
        rec = pyhelper.ImageRecord(zone=1, image_id=1, size=4, next_seq=0x10, lastimage=False, parent=None)
        self.assertTrue(rec.addBufferData(b"\x01\x02", 0x10))
        self.assertFalse(rec.addBufferData(b"\x03\x04\x05", 0x20))
        self.assertFalse(rec.ongoing)
        self.assertEqual(len(rec.buffer), 4)

    def test_image_manager_set_current_does_not_corrupt_zone_and_caps_storage(self) -> None:
        """MED-10: setCurrent must not set current_zone for unknown zones and must cap stored images."""
        mgr = pyhelper.AlImageManager()
        self.assertFalse(mgr.setCurrent(zone=99, unique_id=1, image_id=1, size=10, sequence=0, lastimage=False, totalimages=1))
        self.assertIsNone(mgr.current_zone)

        mgr.create(zone=1, count=11)
        for img_id in range(25):
            mgr.ImageZone[1].current_image = None
            mgr.current_zone = None
            ok = mgr.setCurrent(zone=1, unique_id=1, image_id=img_id, size=10, sequence=0, lastimage=False, totalimages=25)
            self.assertTrue(ok)
        self.assertLessEqual(len(mgr.ImageZone[1].images), 16)


if __name__ == "__main__":
    unittest.main()
