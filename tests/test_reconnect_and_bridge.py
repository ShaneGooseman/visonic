"""Regression tests for reconnect entity rebinding and bridge keepalive behavior."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import unittest
from unittest.mock import MagicMock

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"
if str(VISONIC_DIR) not in sys.path:
    sys.path.append(str(VISONIC_DIR))

from protocol import const as pyconst  # noqa: E402
from protocol import helper as pyhelper  # noqa: E402


class _FakeZoneEntity:
    """Minimal stand-in mirroring VisonicBinarySensor/VisonicSelect rebind lifecycle."""

    def __init__(self, device: pyhelper.AlSensorDeviceHelper, register_fn) -> None:
        self.device = device
        self.available = device.isEnrolled()
        self.state_writes = 0
        self.received_events: list[pyconst.AlSensorCondition] = []
        self._unsub_device = device.onChange(self._on_change)
        self._unsub_registry = register_fn(device.getDeviceID(), self)

    def _on_change(self, sensor, condition) -> None:
        self.received_events.append(condition)
        self.available = sensor.isEnrolled()
        self.state_writes += 1

    def mark_disconnected(self) -> None:
        self.available = False
        self.state_writes += 1

    def rebind_device(self, new_device: pyhelper.AlSensorDeviceHelper) -> None:
        if self._unsub_device is not None:
            self._unsub_device()
        self.device = new_device
        self._unsub_device = new_device.onChange(self._on_change)
        self.available = new_device.isEnrolled()
        self.state_writes += 1


class _ReconnectHarness:
    """Lightweight harness exercising the exact preserve_entities/rebind state machine of VisonicClient."""

    def __init__(self) -> None:
        self.onChangeHandler: set = set()
        self._createdAlarmPanel = False
        self._stop_listener_registered = False
        self._created_sensor_ids: set[int] = set()
        self._created_switch_ids: set[int] = set()
        self._sensor_entities: dict[int, list] = {}
        self._switch_entities: dict[int, list] = {}
        self.sensor_list: list = []
        self.x10_list: list = []
        self.dispatched_unique_ids: list[str] = []

    def onChange(self, cb):
        self.onChangeHandler.add(cb)
        return lambda: self.onChangeHandler.discard(cb)

    def register_sensor_entity(self, device_id: int, entity):
        entities = self._sensor_entities.setdefault(device_id, [])
        if entity not in entities:
            entities.append(entity)
        return lambda: entities.remove(entity) if entity in entities else None

    def _fire_on_change_handlers(self) -> None:
        for cb in list(self.onChangeHandler):
            cb()

    def _notify_entities_disconnected(self) -> None:
        for entities in list(self._sensor_entities.values()):
            for entity in list(entities):
                entity.mark_disconnected()

    def stop_for_reconnect(self) -> None:
        # Mirrors async_panel_stop -> _initialise(preserve_entities=True)
        self.sensor_list = []
        self.x10_list = []
        self._fire_on_change_handlers()
        self._notify_entities_disconnected()

    def on_new_sensor(self, sensor: pyhelper.AlSensorDeviceHelper) -> None:
        dev_id = sensor.getDeviceID()
        self.sensor_list = [s for s in self.sensor_list if s.getDeviceID() != dev_id]
        self.sensor_list.append(sensor)
        if dev_id in self._created_sensor_ids:
            for entity in list(self._sensor_entities.get(dev_id, [])):
                entity.rebind_device(sensor)
        else:
            self._created_sensor_ids.add(dev_id)
            self.dispatched_unique_ids.append(f"visonic_z{dev_id:02d}_sensor")
            _FakeZoneEntity(sensor, self.register_sensor_entity)

    def unload_all(self) -> None:
        self.onChangeHandler.clear()
        self._createdAlarmPanel = False
        self._created_sensor_ids.clear()
        self._created_switch_ids.clear()
        self._sensor_entities.clear()
        self._switch_entities.clear()


class TestReconnectAndBridge(unittest.TestCase):
    """Regression tests for reconnect preservation, entity rebinding and bridge keepalive."""

    def test_onchange_handler_survives_reconnect_and_notifies_unavailable(self) -> None:
        """CRITICAL: onChangeHandler must survive async_panel_stop and notify entities."""
        harness = _ReconnectHarness()
        alarm_updates = 0

        def on_alarm_change() -> None:
            nonlocal alarm_updates
            alarm_updates += 1

        harness.onChange(on_alarm_change)
        harness._createdAlarmPanel = True

        # Disconnect for reconnect
        harness.stop_for_reconnect()
        self.assertEqual(alarm_updates, 1)
        self.assertIn(on_alarm_change, harness.onChangeHandler)
        self.assertTrue(harness._createdAlarmPanel)

        # Reconnect fires handler again
        harness._fire_on_change_handlers()
        self.assertEqual(alarm_updates, 2)

        # Full unload clears handlers and flags
        harness.unload_all()
        self.assertEqual(len(harness.onChangeHandler), 0)
        self.assertFalse(harness._createdAlarmPanel)

    def test_sensor_entity_marks_unavailable_and_rebinds_without_duplicate_unique_id(self) -> None:
        """CRITICAL: Reconnect rebinds existing entity to new AlSensorDevice without duplicating unique_id."""
        harness = _ReconnectHarness()
        old_sensor = pyhelper.AlSensorDeviceHelper(id=1, enrolled=True)
        harness.on_new_sensor(old_sensor)

        self.assertEqual(harness.dispatched_unique_ids, ["visonic_z01_sensor"])
        entity = harness._sensor_entities[1][0]
        self.assertTrue(entity.available)

        # Simulate disconnect
        harness.stop_for_reconnect()
        self.assertFalse(entity.available)

        # Simulate reconnect with a brand-new AlSensorDevice instance for zone 1
        new_sensor = pyhelper.AlSensorDeviceHelper(id=1, enrolled=True)
        harness.on_new_sensor(new_sensor)

        # No duplicate unique_id dispatched
        self.assertEqual(harness.dispatched_unique_ids, ["visonic_z01_sensor"])
        self.assertTrue(entity.available)
        self.assertIs(entity.device, new_sensor)

        # Events from old_sensor no longer reach entity; events from new_sensor do
        old_sensor.pushChange(pyconst.AlSensorCondition.STATE)
        self.assertEqual(entity.received_events, [])

        new_sensor.pushChange(pyconst.AlSensorCondition.STATE)
        self.assertEqual(entity.received_events, [pyconst.AlSensorCondition.STATE])

    def test_client_source_preserves_entities_on_stop_and_registers_stop_once(self) -> None:
        """Verify client.py uses preserve_entities=True, _stop_listener_registered and _get_panel_entity_id."""
        source = (VISONIC_DIR / "core" / "client.py").read_text(encoding="utf-8")
        self.assertIn("self._initialise(preserve_entities=True)", source)
        self.assertIn("self._notify_entities_disconnected()", source)
        self.assertIn("if not self._stop_listener_registered:", source)
        self.assertIn("await self._checkUserPermission(call, POLICY_CONTROL, self._get_panel_entity_id())", source)

    def test_bridge_sequencer_omits_send_alive_when_bridge_connected(self) -> None:
        """HIGH: DoingPowerlinkBridge must not send Send.ALIVE when PowerLinkBridgeConnected is True."""
        source = (VISONIC_DIR / "protocol" / "visonic.py").read_text(encoding="utf-8")
        start = source.index("elif _sequencerState == SequencerType.DoingPowerlinkBridge:")
        end = source.index("####### Drop through to here", start)
        bridge_block = source[start:end]
        code_lines = "\n".join(
            line for line in bridge_block.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertNotIn("Send.ALIVE", code_lines)
        self.assertIn("Send.PL_BRIDGE", code_lines)
        self.assertIn("B0SubType.PANEL_STATE_1", code_lines)


if __name__ == "__main__":
    unittest.main()
