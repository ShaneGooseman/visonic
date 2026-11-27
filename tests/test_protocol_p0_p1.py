"""Regression tests for P0 and P1 fixes in the Visonic protocol layer."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import sys
import unittest

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"
if str(VISONIC_DIR) not in sys.path:
    # Append (do not insert at 0) so custom_components/visonic/select.py does not shadow stdlib select.
    sys.path.append(str(VISONIC_DIR))

from protocol import const as pyconst  # noqa: E402
from protocol import eprom as pyeprom  # noqa: E402
from protocol import helper as pyhelper  # noqa: E402
from protocol import visonic as pyvisonic  # noqa: E402


class TestProtocolP0P1(unittest.TestCase):
    """Protocol-level regression tests (no Home Assistant dependency required)."""

    def test_insert_options_does_not_mutate_global_template(self) -> None:
        """CRIT-01: insertOptions must not mutate pmSendMsg templates in-place."""
        cmd = pyvisonic.pmSendMsg[pyvisonic.Send.ARM]
        original = bytearray(cmd.data)
        entry = pyvisonic.VisonicListEntry(
            command=cmd,
            options=[[3, bytearray([0x12, 0x34])]],
        )
        rendered = entry.insertOptions(cmd.data)

        self.assertEqual(rendered[3:5], bytearray([0x12, 0x34]))
        self.assertEqual(cmd.data, original)
        self.assertIsNot(rendered, cmd.data)

    def test_get_event_data_partition_zero_bounds(self) -> None:
        """HIGH-05: getEventData(0) must use 0-based index and handle empty or partition-3 sets."""
        proto = object.__new__(pyvisonic.VisonicProtocol)
        proto.PartitionState = [
            pyhelper.PartitionStateClass(1),
            pyhelper.PartitionStateClass(2),
            pyhelper.PartitionStateClass(3),
        ]
        proto.getPartitionsInUse = lambda: {3}
        data = proto.getEventData(0)
        self.assertIsInstance(data, dict)

        proto.getPartitionsInUse = lambda: set()
        self.assertEqual(proto.getEventData(0), {})

    def test_panel_trouble_status_restores_to_none(self) -> None:
        """HIGH-06: UpdatePanelState must clear PanelTroubleStatus on restore events."""
        ps = pyhelper.PartitionStateClass(1)
        ps.PanelTroubleStatus = pyconst.AlTroubleType.BATTERY
        restore_event = next(iter(pyhelper.pmPanelTroubleType_r))
        ps.UpdatePanelState(restore_event, 1)
        self.assertEqual(ps.PanelTroubleStatus, pyconst.AlTroubleType.NONE)

    def test_visonic_list_entry_str_obfuscates_secrets(self) -> None:
        """HIGH-07: VisonicListEntry.__str__ must not leak PIN/DownloadCode when OBFUS is True."""
        self.assertTrue(pyvisonic.OBFUS)
        cmd = pyvisonic.pmSendMsg[pyvisonic.Send.ARM]
        entry = pyvisonic.VisonicListEntry(
            command=cmd,
            options=[[3, bytearray([0x12, 0x34])]],
        )
        text = str(entry)
        self.assertIn("OBFUSCATED", text)
        self.assertNotIn("12", text)
        self.assertNotIn("34", text)

        raw_entry = pyvisonic.VisonicListEntry(raw=bytearray([0x0D, 0xB0, 0x56, 0x78, 0x0A]))
        raw_text = str(raw_entry)
        self.assertIn("OBFUSCATED", raw_text)
        self.assertNotIn("56", raw_text)

    def test_eprom_sensitive_fields_hidden_by_default(self) -> None:
        """HIGH-07: Sensitive EPROM fields must not have show=True."""
        for key in ("duress", "centralStation", "accountNo", "pagerNr", "pagerPIN"):
            self.assertIn(key, pyeprom.pmDecodePanelSettings)
            self.assertFalse(
                pyeprom.pmDecodePanelSettings[key].show,
                f"EPROM setting '{key}' should not be exposed in attributes",
            )

    def test_jpeg_dimensions_parser_without_pillow(self) -> None:
        """HIGH-11: _get_jpeg_dimensions parses SOF0 header in pure Python and rejects corrupt data."""
        # Minimal valid JPEG SOI + SOF0 segment for 320x240 (0x0140 x 0x00F0)
        jpeg_bytes = bytes([
            0xFF, 0xD8,              # SOI
            0xFF, 0xC0,              # SOF0
            0x00, 0x0B,              # length = 11
            0x08,                    # precision
            0x00, 0xF0,              # height = 240
            0x01, 0x40,              # width = 320
            0x01, 0x01, 0x11, 0x00,  # component data
            0xFF, 0xD9,              # EOI
        ])
        self.assertEqual(pyvisonic.PacketHandling._get_jpeg_dimensions(jpeg_bytes), (320, 240))
        self.assertIsNone(pyvisonic.PacketHandling._get_jpeg_dimensions(b"not a jpeg"))
        self.assertIsNone(pyvisonic.PacketHandling._get_jpeg_dimensions(b"\xff\xd8\xff\xc0\x00\x02"))

    def test_unknown_f4_subtype_does_not_raise_key_error(self) -> None:
        """HIGH-11: Unknown 0xF4 subtype must fall back safely instead of raising KeyError: 0."""
        proto = object.__new__(pyvisonic.VisonicProtocol)
        proto.suspendAllOperations = False
        proto.ReceiveData = bytearray([0x0D, 0xF4])
        proto.pmCurrentPDU = pyvisonic.pmReceiveMsg[pyvisonic.Receive.IMAGE_DATA]
        proto.pmIncomingPduLen = 0
        proto.pmFlexibleLength = 0
        proto.resetMessageData = lambda: None
        proto._handle_received_byte(0x99)
        self.assertEqual(proto.pmCurrentPDU, pyvisonic.pmReceiveMsg[0])

    def test_translations_json_valid_and_contain_abort_key(self) -> None:
        """MED-13: All translation files must be valid JSON and define config.abort.cannot_connect_refused."""
        trans_dir = VISONIC_DIR / "translations"
        files = sorted(trans_dir.glob("*.json"))
        self.assertGreaterEqual(len(files), 4)
        for file_path in files:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            self.assertIn(
                "cannot_connect_refused",
                data["config"]["abort"],
                f"Missing config.abort.cannot_connect_refused in {file_path.name}",
            )


if __name__ == "__main__":
    unittest.main()
