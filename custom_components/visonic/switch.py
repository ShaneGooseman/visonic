"""Switches for the connection to a Visonic PowerMax or PowerMaster Alarm System."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, cached_property, callback
from homeassistant.util import slugify
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import VisonicConfigEntry
from .protocol.const import AlX10Command, AlSwitchDevice
from .core.client import VisonicClient
from .const import (
    DOMAIN,
    VISONIC_TRANSLATION_KEY,
    PANEL_ATTRIBUTE_NAME,
    MANUFACTURER,
    DEVICE_ATTRIBUTE_NAME,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: VisonicConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Visonic X10 Switch."""
    #_LOGGER.debug(f"[async_setup_entry] start")

    @callback
    def async_add_switch(device: AlSwitchDevice) -> None:
        """Add Visonic Switch."""
        _LOGGER.debug(f"[async_setup_entry] adding {device.getDeviceID()}")
        entities: list[SwitchEntity] = []
        entities.append(VisonicSwitch(hass, entry.runtime_data.client, device))
        async_add_entities(entities)

    entry.runtime_data.dispatchers[SWITCH_DOMAIN] = async_dispatcher_connect(hass, f"{DOMAIN}_{entry.entry_id}_add_{SWITCH_DOMAIN}", async_add_switch )
    #_LOGGER.debug("[async_setup_entry] exit")


class VisonicSwitch(SwitchEntity):
    """Representation of a Visonic X10 Switch."""

    _attr_translation_key: str = VISONIC_TRANSLATION_KEY
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, client: VisonicClient, visonic_device: AlSwitchDevice):
        """Initialise a Visonic X10 Device."""
        _LOGGER.debug("[VisonicSwitch] Creating X10 Switch %s", visonic_device.id)
        self._client = client
        self._visonic_device = visonic_device
        self._unsub_device = self._visonic_device.onChange(self.onChange)
        self._unsub_registry = client.register_switch_entity(visonic_device.getDeviceID(), self)
        self._x10id = self._visonic_device.getDeviceID()
        self._panel = client.getPanelID()
        self._current_value = self._visonic_device.isOn()

        self._dname = self._visonic_device.createFriendlyName()
        pname = client.getMyString()
        self._name = str(pname + self._dname).lower()
        self._is_available = True
        self._attr_unique_id = slugify(self._name + "_switch")
        self._attr_name = None
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._name)},
            manufacturer=MANUFACTURER,
        )

    # Called when an entity is about to be removed from Home Assistant. Example use: disconnect from the server or unsubscribe from updates.
    async def async_will_remove_from_hass(self):
        """Remove from hass."""
        _LOGGER.debug(f"[async_will_remove_from_hass] id = {self.unique_id}")
        if self._unsub_device is not None:
            self._unsub_device()
            self._unsub_device = None
        if self._unsub_registry is not None:
            self._unsub_registry()
            self._unsub_registry = None
        self._visonic_device = None
        self._is_available = False
        self._client = None
        await super().async_will_remove_from_hass()

    def mark_disconnected(self) -> None:
        """Mark switch entity unavailable while panel connection is down."""
        self._is_available = False
        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()

    def rebind_device(self, switch: AlSwitchDevice) -> None:
        """Re-bind switch entity to a new AlSwitchDevice instance after reconnect."""
        if self._unsub_device is not None:
            self._unsub_device()
        self._visonic_device = switch
        self._unsub_device = self._visonic_device.onChange(self.onChange)
        self._current_value = self._visonic_device.isOn()
        self._is_available = True
        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()

    @cached_property
    def name(self) -> str | None:
        """Name."""
        return None

    def onChange(self, switch : AlSwitchDevice):
        """Switch state has changed."""
        # the switch parameter is the same as self._visonic_device, but it's a generic callback handler that cals this function
        if self._visonic_device is None:
            return
        _LOGGER.debug("[onChange] Switch changeHandler %s", str(self._name))
        self._current_value = self._visonic_device.isOn()
        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        #_LOGGER.debug(f"   In binary sensor VisonicSensor available self._is_available = {self._is_available}    self._current_value = {self._current_value}")
        return self._is_available

    @property
    def assumed_state(self):
        """Return False if unable to access real state of entity."""
        return False

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._current_value

    async def async_turn_on(self, **kwargs):
        """Turn the device on."""
        self.turnmeonandoff(AlX10Command.ON)

    async def async_turn_off(self, **kwargs):
        """Turn the device off."""
        self.turnmeonandoff(AlX10Command.OFF)

    def isPanelConnected(self) -> bool:
        """Are we connected to the Alarm Panel."""
        # If we are starting up or have been removed then assume we need a valid code
        #_LOGGER.debug(f"alarm control panel isPanelConnected {self.entity_id=}")
        if self._client is None:
            return False
        return self._client.isPanelConnected()

    # "off"  "on"  "dimmer"  "brighten"
    def turnmeonandoff(self, state : AlX10Command):
        """Send disarm command."""
        if not self.isPanelConnected():
            raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="no_panel_connection",
                    translation_placeholders={
                        "myname": self._client.getAlarmPanelUniqueIdent() if self._client is not None else "<******>"
                    }
                )
        self._client.sendX10(self._x10id, state)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}
        if self._visonic_device is not None:
            attr["location"] = self._visonic_device.getLocation()
            attr["type"] = self._visonic_device.getType()
            attr[DEVICE_ATTRIBUTE_NAME] = self._visonic_device.getDeviceID()
        attr["name"] = self._dname
        attr[PANEL_ATTRIBUTE_NAME] = self._panel
        return attr
