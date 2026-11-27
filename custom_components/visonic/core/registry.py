"""Device Registry and Entity Registry reconciliation helpers for Visonic panels."""

from __future__ import annotations

import re
from typing import Any, Callable

try:
    from homeassistant.helpers import device_registry as dr, entity_registry as er
    from homeassistant.util import slugify
except ImportError:  # pragma: no cover - allows pure unit testing without Home Assistant
    dr = None
    er = None

    def slugify(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def build_panel_device_identifiers(
    panel_ident: str,
    prefix: str,
    sensor_list: list[Any],
    x10_list: list[Any],
) -> set[str]:
    """Build the set of active DeviceRegistry identifier strings owned by a panel."""
    active: set[str] = {panel_ident, slugify(panel_ident)}
    for sensor in sensor_list:
        active.add(prefix + sensor.createFriendlyName().lower())
    for switch in x10_list:
        active.add(prefix + switch.createFriendlyName().lower())
    return active


def filter_devices_by_panel_prefix(devices: list[Any], prefix: str) -> list[Any]:
    """Filter DeviceEntry objects belonging to zones, X10 switches or PGM of a specific panel prefix."""
    pattern = re.compile(f"^{re.escape(prefix)}([xz]\\d\\d|pgm)$")
    matched: list[Any] = []
    for device in devices:
        for ident in device.identifiers:
            if len(ident) >= 2 and pattern.search(str(ident[1])):
                matched.append(device)
                break
    return matched


def rationalise_panel_devices(
    hass: Any,
    entry_id: str,
    panel_ident: str,
    prefix: str,
    sensor_list: list[Any],
    x10_list: list[Any],
    log_debug: Callable[[str], None],
) -> int:
    """Remove stale zone/X10/PGM devices and their entities that are no longer reported by the panel."""
    my_entities = build_panel_device_identifiers(panel_ident, prefix, sensor_list, x10_list)
    log_debug(f"     Set of Current Devices From Panel {my_entities}")

    entity_reg = er.async_get(hass)
    device_reg = dr.async_get(hass)

    device_entries = dr.async_entries_for_config_entry(device_reg, entry_id)
    device_entries = filter_devices_by_panel_prefix(device_entries, prefix)

    removed_count = 0
    for device in device_entries:
        entity_entries = er.async_entries_for_device(entity_reg, device.id, True)
        for ident in device.identifiers:
            if ident[1] not in my_entities:
                log_debug("               Deleting this device from HA")
                for entity in entity_entries:
                    log_debug(f"                     Deleting this entity from HA {entity}")
                    entity_reg.async_remove(entity.entity_id)
                device_reg.async_remove_device(device.id)
                removed_count += 1
                break
    return removed_count
