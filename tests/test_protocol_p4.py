"""Regression tests for P4 fixes (truncated packets, EPROM bounds, peek_nowait, reconfigure translations)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import unittest

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"
if str(VISONIC_DIR) not in sys.path:
    sys.path.append(str(VISONIC_DIR))

from protocol import eprom as pyeprom  # noqa: E402
from protocol import visonic as pyvisonic  # noqa: E402


class TestProtocolP4(unittest.TestCase):
    """P4 regression tests for packet bounds, EPROM validation and queue peek."""

    def test_truncated_packets_do_not_raise_index_error(self) -> None:
        """MED-12: Message handlers must safely ignore truncated packets."""
        proto = object.__new__(pyvisonic.VisonicProtocol)
        proto._handle_msgtype25(bytearray(b"\x01"))
        proto._handle_msgtype3C(bytearray(b"\x01\x02"))
        proto._handle_msgtypeA0(bytearray(b"\x01\x02"))
        proto._handle_msgtypeA5(bytearray(b"\x01\x02"))
        proto._handle_msgtypeA7(bytearray(b"\x01\x02"))
        self.assertFalse(proto._handle_msgtypeAB(bytearray()))
        proto._handle_msgtypeE0(bytearray(b"\x01\x02"))
        self.assertFalse(proto._handle_msgtypeF4(bytearray(b"\x03")))

    def test_eprom_save_rejects_out_of_range_page_and_index(self) -> None:
        """MED-12: EPROMManager.saveEPROMSettings must ignore invalid page/index values."""
        mgr = pyeprom.EPROMManager()
        mgr.saveEPROMSettings(-1, 0, bytearray(b"\x01\x02"))
        mgr.saveEPROMSettings(300, 0, bytearray(b"\x01\x02"))
        mgr.saveEPROMSettings(1, -5, bytearray(b"\x01\x02"))
        mgr.saveEPROMSettings(1, 256, bytearray(b"\x01\x02"))
        self.assertEqual(mgr.pmRawSettings, {})

    def test_priority_queue_peek_nowait_raises_queue_empty(self) -> None:
        """LOW-02: PriorityQueueWithPeek.peek_nowait must raise asyncio.QueueEmpty when empty."""
        q = pyvisonic.PriorityQueueWithPeek()
        with self.assertRaises(asyncio.QueueEmpty):
            q.peek_nowait()

    def test_translations_contain_reconfigure_step(self) -> None:
        """INFO-02: All translation files must define config.step.reconfigure."""
        trans_dir = VISONIC_DIR / "translations"
        for file_path in sorted(trans_dir.glob("*.json")):
            data = json.loads(file_path.read_text(encoding="utf-8"))
            self.assertIn(
                "reconfigure",
                data["config"]["step"],
                f"Missing config.step.reconfigure in {file_path.name}",
            )


if __name__ == "__main__":
    unittest.main()
