"""Regression tests for P2 fixes (callbacks, shutdown, timers and timeouts)."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"
if str(VISONIC_DIR) not in sys.path:
    sys.path.append(str(VISONIC_DIR))

import pyconst  # noqa: E402
import pyhelper  # noqa: E402
import pyvisonic  # noqa: E402


class TestProtocolP2(unittest.TestCase):
    """P2 regression tests for callbacks, partition timers and shutdown."""

    def test_sensor_onchange_unsubscribe_keeps_other_listeners(self) -> None:
        """HIGH-08: Unsubscribing one sensor listener must not clear other listeners."""
        sensor = pyhelper.AlSensorDeviceHelper(id=1)
        received_a: list = []
        received_b: list = []

        unsub_a = sensor.onChange(lambda s, c: received_a.append(c))
        unsub_b = sensor.onChange(lambda s, c: received_b.append(c))

        sensor.pushChange(pyconst.AlSensorCondition.STATE)
        self.assertEqual(len(received_a), 1)
        self.assertEqual(len(received_b), 1)

        unsub_a()
        sensor.pushChange(pyconst.AlSensorCondition.STATE)
        self.assertEqual(len(received_a), 1)
        self.assertEqual(len(received_b), 2)

        unsub_b()
        sensor.pushChange(pyconst.AlSensorCondition.STATE)
        self.assertEqual(len(received_b), 2)

    def test_switch_onchange_unsubscribe_keeps_other_listeners(self) -> None:
        """HIGH-08: Unsubscribing one switch listener must not clear other listeners."""
        sw = pyhelper.AlSwitchDeviceHelper(id=1)
        received_a: list = []
        received_b: list = []

        unsub_a = sw.onChange(lambda s: received_a.append(s.getDeviceID()))
        unsub_b = sw.onChange(lambda s: received_b.append(s.getDeviceID()))

        sw.pushChange()
        self.assertEqual(received_a, [1])
        self.assertEqual(received_b, [1])

        unsub_a()
        sw.pushChange()
        self.assertEqual(received_a, [1])
        self.assertEqual(received_b, [1, 1])

        unsub_b()

    def test_shutdown_cancels_existing_partition_states_before_reinit(self) -> None:
        """HIGH-10: shutdownOperation must call shutdownOperation on old PartitionState instances."""
        helper = object.__new__(pyvisonic.VisonicProtocol)
        helper.loop = MagicMock()
        old_partitions = [MagicMock(), MagicMock(), MagicMock()]
        helper.PartitionState = old_partitions

        pyhelper.AlPanelInterfaceHelper.shutdownOperation(helper)

        for part in old_partitions:
            part.shutdownOperation.assert_called_once()
        self.assertIsNot(helper.PartitionState, old_partitions)

    def test_update_partition_disarm_stops_intruder_timer(self) -> None:
        """HIGH-10: Disarming while SirenActive is True must stop IntruderTimeTask."""
        ps = pyhelper.PartitionStateClass(MagicMock())
        ps.SirenActive = True
        ps.PanelIntruderStatus = True
        ps.stopIntruderStateTimer = MagicMock()

        ps.UpdatePartition(sysStatus=0x00, sysFlags=0x00, PanelMode=pyconst.AlPanelMode.POWERLINK)

        self.assertFalse(ps.SirenActive)
        self.assertFalse(ps.PanelIntruderStatus)
        ps.stopIntruderStateTimer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
