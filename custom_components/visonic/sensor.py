"""Create a connection to a Visonic PowerMax or PowerMaster Alarm System and Create a Simple Entity to Report Status only."""

import logging
from enum import IntEnum
from homeassistant.util import slugify
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.core import HomeAssistant, callback
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import LIGHT_LUX, UnitOfTemperature
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.alarm_control_panel import AlarmControlPanelState

# Use the standard HA core attributes, alarm states and services to report status
from homeassistant.const import (
#    STATE_ALARM_ARMED_AWAY,
#    STATE_ALARM_ARMED_HOME,
#    STATE_ALARM_ARMING,
#    STATE_ALARM_DISARMED,
#    STATE_ALARM_PENDING,
#    STATE_ALARM_TRIGGERED,
    STATE_UNKNOWN,
)

from .core.client import VisonicClient
from . import VisonicConfigEntry
from .const import (
    DOMAIN,
    VISONIC_TRANSLATION_KEY,
    map_panel_status_to_ha_status,
    MANUFACTURER,
    TEXT_LAST_EVENT_NAME,
    PANEL_ATTRIBUTE_NAME,
)

from .protocol.const import AlPanelStatus, AlSensorCondition, AlSensorDevice

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: VisonicConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Visonic Alarm Sensors for Monitor."""
    #_LOGGER.debug(f"[async_setup_entry] start")

    @callback
    def async_add_sensor(payload=False) -> None:
        """Add Visonic panel sensor (minimal mode) or zone measurement sensors (temperature/lux)."""
        entities: list[Entity] = []
        client: VisonicClient = entry.runtime_data.client

        if isinstance(payload, tuple) and len(payload) == 2 and isinstance(payload[0], AlSensorDevice):
            device, kind = payload
            entities.append(VisonicZoneSensor(hass, client, device, kind))
            async_add_entities(entities)
            return

        main_one = bool(payload)
        p = client.getPartitionsInUse()

        if main_one and entry.runtime_data.alarm_entity is None: #  or p is None or (p is not None and len(p) == 1):
            entry.runtime_data.alarm_entity = VisonicSensor(hass, client)
            entities.append(entry.runtime_data.alarm_entity)
            _LOGGER.debug(f"[async_setup_entry] adding main entity for panel {client.getPanelID()}")
        elif entry.runtime_data.alarm_entity is not None and p is not None and len(p) > 1:
            _LOGGER.debug(f"[async_setup_entry] updating main alarm control panel entity for partition set {p}")
            entry.runtime_data.alarm_entity.resetPartition(0)
            for i in p:
                if i != 0:
                    entities.append(VisonicSensor(hass, client, i))
            _LOGGER.debug(f"[async_setup_entry] adding sensor panel entities for partition set {p}")

        if len(entities) > 0:
            async_add_entities(entities, True)

    entry.runtime_data.dispatchers[SENSOR_DOMAIN] = async_dispatcher_connect(hass, f"{DOMAIN}_{entry.entry_id}_add_{SENSOR_DOMAIN}", async_add_sensor)
    #_LOGGER.debug("[async_setup_entry] exit")

class VisonicSensor(SensorEntity):
    """Representation of a Visonic alarm control panel as a simple sensor for minimal."""

    _unrecorded_attributes = frozenset(
        {
            "Panel Model",
            "Watchdog Timeout (Total)",
            "Watchdog Timeout (Past 24 Hours)",
            "Download Timeout",
            "Download Message Retries",
            "Disconnection Count",
            "Client Version",
            "Protocol Version",
            "Power Master",
        }
    )

    def __init__(self, hass: HomeAssistant, client: VisonicClient, partition : int = None):
        """Initialize a Visonic security alarm."""
        self._client = client
        self.hass = hass
        self._attr_native_value = None
        self._attr_should_poll = False
        self._last_triggered = ""
        self.resetPartition(partition)
        self._unsub_client = self._client.onChange(callback = self.onClientChange)
        #_LOGGER.debug(f"[VisonicSensor] Initialising alarm sensor {self._myname}")
        self._attr_unique_id = slugify(self._myname+"_sensor")
        self._attr_name = "Alarm Panel" # self._name
        self._attr_has_entity_name = True
        self._attr_translation_key = VISONIC_TRANSLATION_KEY

    def resetPartition(self, partition : int | None):
        if partition is None:
            self._partition = None           # When partitions are not used then we only use partition 1 for panel state
            self._partitionSet = {1, 2, 3}   # When partitions are not used then we command (Arm, Disarm etc) all partitions
            self._myname = self._client.getAlarmPanelUniqueIdent()
            _LOGGER.debug(f"[VisonicAlarm] Setting primary sensor {self._myname}      {self.unique_id=}")
        elif partition == 0:                 # EXPERIMENTAL
            self._partition = 0              # When partitions are not used then we only use partition 0 for panel state
            self._partitionSet = {1, 2, 3}   # When partitions are not used then we command (Arm, Disarm etc) all partitions
            self._myname = self._client.getAlarmPanelUniqueIdent()
            _LOGGER.debug(f"[VisonicAlarm] Setting sensor {self._myname}      {self.unique_id=}")
        else:
            self._partition = partition
            self._partitionSet = { partition }
            self._myname = self._client.getAlarmPanelUniqueIdent() + " Partition " + str(partition)
            _LOGGER.debug(f"[VisonicAlarm] Setting alarm sensor {self._myname}      {self.unique_id=}")
        self._client.setPartitionNaming(partition = partition, panel_entity_name = self._myname)
        pm = self._client.getPanelModel()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._client.getAlarmPanelUniqueIdent())},
            manufacturer=MANUFACTURER,
            model = pm,
        )

    async def async_will_remove_from_hass(self):
        """Remove from hass."""
        if self._unsub_client is not None:
            self._unsub_client()
            self._unsub_client = None
        panel_id = self._client.getPanelID() if self._client is not None else "unknown"
        _LOGGER.debug(f"[async_will_remove_from_hass] Removing alarm panel sensor {self._myname} panel {panel_id}")
        self._client = None
        await super().async_will_remove_from_hass()

    def isPanelConnected(self) -> bool:
        """Are we connected to the Alarm Panel."""
        # If we are starting up or have been removed then assume we need a valid code
        if self._client is None:
            return False
        return self._client.isPanelConnected()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.isPanelConnected()

    # The callback handler from the client. All we need to do is schedule an update.
    def onClientChange(self):
        """HA Event Callback."""
        if self.hass is not None and self.entity_id is not None:
            self.async_schedule_update_ha_state(True)

    @property
    def changed_by(self):
        """Last change triggered by."""
        return self._last_triggered

    async def async_update(self):
        """Get the state of the device."""
        #_LOGGER.debug(f"[update] before {self._attr_native_value=}")
        self._attr_native_value = None
        self._attr_extra_state_attributes = {}

        if self._client is not None and self.isPanelConnected():
            ptu = self._client.getPartitionsInUse()
            isa, _ = self._client.isSirenActive(None if ptu is None else 0)
            if isa:
                self._attr_native_value = AlarmControlPanelState.TRIGGERED
            else:
                armcode = self._client.getPanelStatus(self._partition)
                if armcode is not None and armcode in map_panel_status_to_ha_status:
                    self._attr_native_value = map_panel_status_to_ha_status[armcode]

            stat = self._client.getPanelStatusDict(self._partition)
            #_LOGGER.debug(f"[update] stat {stat}")

            data = None
            if self._partition is None or self._partition == 0:
                data = self._client.getClientStatusDict()
                if TEXT_LAST_EVENT_NAME in stat and len(stat[TEXT_LAST_EVENT_NAME]) > 2:
                    self._last_triggered = stat[TEXT_LAST_EVENT_NAME]

            if data is not None and stat is not None:
                self._attr_extra_state_attributes = {**stat, **data}
            elif stat is not None:
                self._attr_extra_state_attributes = stat
            elif data is not None:
                self._attr_extra_state_attributes = data
            
            self._attr_extra_state_attributes[PANEL_ATTRIBUTE_NAME] = self._client.getPanelID()
            #_LOGGER.debug(f"[update] _attr_extra_state_attributes {self._attr_extra_state_attributes=}")

        #_LOGGER.debug(f"[update] after {self._attr_state=}")


class VisonicZoneSensor(SensorEntity):
    """Measurement sensor entity for zone temperature or illuminance (lux)."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        hass: HomeAssistant,
        client: VisonicClient,
        sensor: AlSensorDevice,
        kind: str,
    ) -> None:
        """Initialize the zone measurement sensor."""
        self.hass = hass
        self._visonic_device: AlSensorDevice | None = sensor
        self._kind = kind
        dname = sensor.createFriendlyName()
        pname = client.getMyString()
        dev_ident = str(pname + dname).lower()
        self._attr_unique_id = slugify(f"{dev_ident}_{kind}")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, dev_ident)},
            manufacturer=MANUFACTURER,
        )
        if kind == "temperature":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            self._attr_name = "Temperature"
        else:
            self._attr_device_class = SensorDeviceClass.ILLUMINANCE
            self._attr_native_unit_of_measurement = LIGHT_LUX
            self._attr_name = "Illuminance"
        self._unsub_device = self._visonic_device.onChange(self._on_change)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when removed from Home Assistant."""
        if self._unsub_device is not None:
            self._unsub_device()
            self._unsub_device = None
        self._visonic_device = None
        await super().async_will_remove_from_hass()

    def _on_change(self, sensor: AlSensorDevice, condition: AlSensorCondition) -> None:
        """Write updated measurement on sensor change."""
        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if the zone sensor is enrolled."""
        return self._visonic_device is not None and self._visonic_device.isEnrolled()

    @property
    def native_value(self) -> float | int | None:
        """Return the native measurement value."""
        if self._visonic_device is None:
            return None
        if self._kind == "temperature":
            return self._visonic_device.getTemperature()
        return self._visonic_device.getLux()
