"""Diagnostics support for Visonic Integration."""
from __future__ import annotations
import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PATH, CONF_PORT

from . import VisonicConfigEntry
from .const import CONF_DOWNLOAD_CODE
from .client import VisonicClient

_LOGGER = logging.getLogger(__name__)

REDACT_ME = (
    CONF_DOWNLOAD_CODE,
    CONF_HOST,
    CONF_PORT,
    CONF_PATH,
    "Duress",
    "Pager PIN #",
    "1st Account No",
    "2nd Account No",
    "1st Central Tel",
    "2nd Central Tel",
    "Pager Tel Number",
)

def _redact_log_lines(lines: list[str], secrets: list[str]) -> list[str]:
    """Redact sensitive connection strings from client log lines."""
    filtered_secrets = [str(s) for s in secrets if s]
    if not filtered_secrets:
        return lines
    redacted = []
    for line in lines:
        clean = line
        for secret in filtered_secrets:
            if secret in clean:
                clean = clean.replace(secret, "**REDACTED**")
        redacted.append(clean)
    return redacted

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: VisonicConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics."""
    diagdata = {}
    cdata = entry.runtime_data
    if cdata.client is not None:
        visonic = { } 
        client : VisonicClient = cdata.client
        B = client.getClientStatusDict()
        if ( piu := client.getPartitionsInUse() ) is not None:
            partition = {}
            partition["panel"] = client.getPanelStatusDict(0)
            for p in piu:
                partition[f"partition {p}"] = client.getPanelStatusDict(p)
            visonic = { **partition, **B } 
            #_LOGGER.error(f"async_get_config_entry_diagnostics {entry.as_dict()} {visonic}")
        else:
            A = client.getPanelStatusDict()
            visonic = { **A, **B } 
            #_LOGGER.error(f"async_get_config_entry_diagnostics {entry.as_dict()} {visonic}")
        diagdata = {
            "entry": entry.as_dict(),
            "client connected": 'yes',
            "panel connected": 'yes' if client.isPanelConnected() else 'no',
            "visonic": visonic,
            "sensor": client.dumpSensorsToStringList(),
            "switch": client.dumpSwitchesToStringList(),
            "clientlog": _redact_log_lines(
                client.getStrLog(),
                [
                    entry.data.get(CONF_HOST, ""),
                    entry.data.get(CONF_PATH, ""),
                    entry.data.get(CONF_DOWNLOAD_CODE, ""),
                    entry.options.get(CONF_HOST, ""),
                    entry.options.get(CONF_PATH, ""),
                    entry.options.get(CONF_DOWNLOAD_CODE, ""),
                ],
            ),
        }
    else:
        diagdata = {
            "entry": entry.as_dict(),
            "client connected": 'no',
            "panel connected": 'no',
        }

    return async_redact_data(diagdata, REDACT_ME)
