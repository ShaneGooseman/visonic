"""Sensors for the connection to a Visonic PowerMax or PowerMaster Alarm System."""

import logging
import asyncio
import re

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant, cached_property, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.util import slugify
from homeassistant.const import (
    ATTR_ARMED,
    ATTR_BATTERY_LEVEL,
    ATTR_LAST_TRIP_TIME,
    ATTR_TRIPPED,
)

from . import VisonicConfigEntry
from .protocol.const import AlSensorDevice, AlSensorType, AlSensorCondition
from .core.client import VisonicClient
from .const import (
    DOMAIN,
    VISONIC_TRANSLATION_KEY,
    SensorEntityFeature,
    PANEL_ATTRIBUTE_NAME,
    MANUFACTURER,
    DEVICE_ATTRIBUTE_NAME,
)

_LOGGER = logging.getLogger(__name__)

# Dictionary mapping between the Pyvisonic sensor type and the HA Sensor Class
_stype_to_ha_sensor_class = {
    AlSensorType.IGNORED     : None,
    AlSensorType.UNKNOWN     : None,
    AlSensorType.MOTION      : BinarySensorDeviceClass.MOTION,
    AlSensorType.CAMERA      : BinarySensorDeviceClass.MOTION,
    AlSensorType.MAGNET      : BinarySensorDeviceClass.WINDOW,
    AlSensorType.WIRED       : BinarySensorDeviceClass.DOOR,
    AlSensorType.SMOKE       : BinarySensorDeviceClass.SMOKE,
    AlSensorType.FLOOD       : BinarySensorDeviceClass.MOISTURE,
    AlSensorType.GAS         : BinarySensorDeviceClass.GAS,
    AlSensorType.VIBRATION   : BinarySensorDeviceClass.VIBRATION, 
    AlSensorType.SHOCK       : BinarySensorDeviceClass.VIBRATION,
    AlSensorType.TEMPERATURE : BinarySensorDeviceClass.HEAT,
    AlSensorType.SOUND       : BinarySensorDeviceClass.SOUND,
    AlSensorType.GLASS_BREAK : BinarySensorDeviceClass.VIBRATION,
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: VisonicConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Visonic Alarm Binary Sensors."""
    #_LOGGER.debug(f"[async_setup_entry] start")

    @callback
    def async_add_binary_sensor(device: AlSensorDevice) -> None:
        """Add Visonic Binary Sensor and diagnostic tamper/battery binary sensors."""
        _LOGGER.debug(f"[async_setup_entry] adding {device.getDeviceID()}")
        client = entry.runtime_data.client
        vbs = VisonicBinarySensor(hass, client, device, entry)
        entities: list[BinarySensorEntity] = [
            vbs,
            VisonicZoneDiagnosticBinarySensor(hass, client, device, "tamper"),
        ]
        if device.getSensorType() != AlSensorType.WIRED:
            entities.append(
                VisonicZoneDiagnosticBinarySensor(hass, client, device, "battery")
            )
        async_add_entities(entities)
        entry.runtime_data.sensors.append(vbs)

    entry.runtime_data.dispatchers[BINARY_SENSOR_DOMAIN] = async_dispatcher_connect( hass, f"{DOMAIN}_{entry.entry_id}_add_{BINARY_SENSOR_DOMAIN}", async_add_binary_sensor )
    #_LOGGER.debug("[async_setup_entry] exit")


#   Each Sensor in Visonic Alarms can be Armed/Bypassed individually
class VisonicBinarySensor(BinarySensorEntity):
    """Representation of a Visonic Sensor."""

    _unrecorded_attributes = frozenset(
        {
            "last_tripped_time",
            "zone_type",
            "zone_chime",
            "sensor_type",
            "model_type",
            "raw_sensor_identifier",
            "partition",
            "zone_enrolled",
        }
    )

    def __init__(self, hass, client: VisonicClient, sensor: AlSensorDevice, entry: VisonicConfigEntry):
        """Initialize the sensor."""
        #_LOGGER.debug("[VisonicBinarySensor]   In binary sensor VisonicSensor initialisation")
        self.hass = hass
        self._client = client
        self.entry = entry

        self._visonic_device = sensor
        self.timerTask = None

        self._dname = sensor.createFriendlyName()
        pname = client.getMyString()
        self._name = str(pname + self._dname).lower()
        _LOGGER.debug(f"[VisonicBinarySensor] friendlyname : {self._name}")
        self._panel = client.getPanelID()
        # Append device id to prevent name clashes in HA.
        self._current_value = (self._visonic_device.isTriggered() or self._visonic_device.isOpen())
        self._is_available = self._visonic_device.isEnrolled()
        self._unsub_device = self._visonic_device.onChange(self.onChange)
        self._attr_unique_id = slugify(f"{self._name}_sensor")
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        self._attr_translation_key = VISONIC_TRANSLATION_KEY
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._name)},
            manufacturer=MANUFACTURER,
        )

    # Called when an entity is about to be removed from Home Assistant. Example use: disconnect from the server or unsubscribe from updates.
    async def async_will_remove_from_hass(self):
        """Remove from hass."""
        _LOGGER.debug(f"[async_will_remove_from_hass] id = {self.unique_id}")
        if self.timerTask is not None:
            _LOGGER.debug(f"[async_will_remove_from_hass] id = {self.unique_id} killing timer task")
            try:
                self.timerTask.cancel()
            except Exception as ex:
                # Do not cause a full Home Assistant Exception, keep it local here
                _LOGGER.debug("[async_will_remove_from_hass]...........             Caused an exception killing timer task")
                _LOGGER.debug(f"[async_will_remove_from_hass]                           {ex}")   
        if self._unsub_device is not None:
            self._unsub_device()
            self._unsub_device = None
        self._visonic_device = None
        self._is_available = False
        self._client = None
        await super().async_will_remove_from_hass()

    async def _retainStateTimout(self):
        if self._client is None:
            self.timerTask = None
            return
        timeout = self._client.getSensorOnDelay(self.device_class)
        _LOGGER.debug(f"[_retainStateTimout] in   id = {self.unique_id}   timeout = {timeout}    dc={self.device_class}")
        try:
            await asyncio.sleep(timeout)
            if self._visonic_device is not None:
                self._current_value = self._visonic_device.isTriggered() or self._visonic_device.isOpen()
                self._is_available = self._visonic_device.isEnrolled()
            if self.hass is not None and self.entity_id is not None:
                self.async_write_ha_state()
            _LOGGER.debug(f"[_retainStateTimout] out  id = {self.unique_id}   timeout = {timeout}    current = {self._current_value}")
        finally:
            self.timerTask = None

    def onChange(self, sensor : AlSensorDevice, s : AlSensorCondition):
        """Call on any change to the sensor."""
        # the sensor parameter is the same as self._visonic_device, but it's a generic callback handler that cals this function
        # Update the current value based on the device state
        #_LOGGER.debug(f"[onChange]   In binary sensor VisonicSensor onchange {self._visonic_device}   self.checking_for_camera_type={self.checking_for_camera_type}")
        if self.hass is not None and self._visonic_device is not None:

            if self.timerTask is None:
                newval = self._visonic_device.isTriggered() or self._visonic_device.isOpen()
                if newval and not self._current_value:
                    # kick off timer
                    self.timerTask = self.hass.async_create_task(self._retainStateTimout())
                self._current_value = newval

            self._is_available = self._visonic_device.isEnrolled()
            _LOGGER.debug(f"[onChange] id = {self.unique_id}   self._is_available = {self._is_available}    self._current_value = {self._current_value}")
            # Ask HA to write the updated state
            if self.entity_id is not None:
                self.async_write_ha_state()
        else:
            _LOGGER.debug("[onChange] called but sensor is not defined")

    def getDeviceID(self) -> int:
        if self._visonic_device is not None:
            return self._visonic_device.getDeviceID()
        return 0

    @cached_property
    def name(self) -> str | None:
        """Name."""
        return "Zone"

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._current_value

    @property
    def supported_features(self) -> int:
        return SensorEntityFeature.BYPASS_FEATURE | SensorEntityFeature.ARMED_FEATURE

    @property
    def device_class(self):
        """Return the class of this sensor."""
        if self._visonic_device is not None:
            stype = self._visonic_device.getSensorType()
            #_LOGGER.debug(f"[device_class] device_class self._is_available = {self._is_available}    self._current_value = {self._current_value}   stype = {stype}")
            if stype is not None and stype in _stype_to_ha_sensor_class:                
                return _stype_to_ha_sensor_class[stype]
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        #_LOGGER.debug(f"   In binary sensor VisonicSensor available self._is_available = {self._is_available}    self._current_value = {self._current_value}")
        return self._is_available

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        # _LOGGER.debug("in extra_state_attributes")
        if self._client is not None and self._visonic_device is not None:
            stype = self._visonic_device.getSensorType()

            attr = {}
            attr["device_name"] = self._dname

            if (t := self._visonic_device.isTamper()) is None:
                attr["device_tamper"] = "undefined"
            else:
                attr["device_tamper"] = t

            attr[ATTR_ARMED] = not self._visonic_device.isBypass()

            attr[ATTR_TRIPPED] = self._visonic_device.isTriggered()
            
            if self._visonic_device.getLastTriggerTime() is None:
                attr[ATTR_LAST_TRIP_TIME] = "unknown"
            else:
                tm = self._visonic_device.getLastTriggerTime() # .strftime("%d/%m/%Y, %H:%M:%S")
                #tm = self._visonic_device.getLastTriggerTime().isoformat()
                # miss off the decimal hundredths seconds onwards
                #tm = tm.replace("T", " ")[0:21]
                attr[ATTR_LAST_TRIP_TIME] = tm
                # attr[ATTR_LAST_TRIP_TIME] = self.pmTimeFunctionStr(self.triggertime)
            
            if stype != AlSensorType.MOTION and stype != AlSensorType.CAMERA:
                attr["zone_open"] = self._visonic_device.isOpen()

            if (t := self._visonic_device.isZoneTamper()) is None:
                attr["zone_tamper"] = "undefined"
            else:
                attr["zone_tamper"] = t
            
            #attr["zone type"] = self.ztype
            zn = self._visonic_device.getZoneLocation()
            if len(zn) == 2:
                attr["zone_name"] = zn[0]
                attr["zone_name_panel"] = "Unknown" if zn[1] is None else zn[1]

            attr["zone_type"] = self._visonic_device.getZoneType()
            attr["zone_chime"] = self._visonic_device.getChimeType()
            attr["zone_trouble"] = self._visonic_device.getProblem()
            if self._client.isPowerMaster():
                attr["zone_missing"] = self._visonic_device.isMissing()
                attr["zone_oneway"] = self._visonic_device.isOneWay()
                attr["zone_inactive"] = self._visonic_device.isInactive()
            
            if (l := self._visonic_device.getLux()) is not None:
                attr["zone_lux"] = l

            if (t := self._visonic_device.getTemperature()) is not None:
                attr["zone_temperature"] = t
            
            if self._client.isPowerMaster() and self._visonic_device.getMotionDelayTime() is not None and len(str(self._visonic_device.getMotionDelayTime())) > 0:
                attr["zone_motion_off_time"] = self._visonic_device.getMotionDelayTime()

            attr[DEVICE_ATTRIBUTE_NAME] = self._visonic_device.getDeviceID()

            if stype != AlSensorType.UNKNOWN:
                attr["sensor_type"] = str(stype).lower()
            elif self._visonic_device.getRawSensorIdentifier() is not None:
                attr["sensor_type"] = "Undefined " + str(self._visonic_device.getRawSensorIdentifier())
            else:
                attr["sensor_type"] = "unknown"

            if stype is not None and stype != AlSensorType.WIRED:
                attr[ATTR_BATTERY_LEVEL] = 0 if self._visonic_device.isLowBattery() else 100

            if self._client.getPartitionsInUse() is not None:   # Returns None when partitions not in use
                if (p := self._visonic_device.getPartition()) is not None:
                    attr["partition"] = list(p)

            attr[PANEL_ATTRIBUTE_NAME] = self._panel
            return attr
            
        return { }


class VisonicZoneDiagnosticBinarySensor(BinarySensorEntity):
    """Diagnostic binary sensor for zone tamper or low battery."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        hass: HomeAssistant,
        client: VisonicClient,
        sensor: AlSensorDevice,
        kind: str,
    ) -> None:
        """Initialize the diagnostic zone binary sensor."""
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
        if kind == "tamper":
            self._attr_device_class = BinarySensorDeviceClass.TAMPER
            self._attr_name = "Tamper"
        else:
            self._attr_device_class = BinarySensorDeviceClass.BATTERY
            self._attr_name = "Battery"
        self._unsub_device = self._visonic_device.onChange(self._on_change)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe when removed from Home Assistant."""
        if self._unsub_device is not None:
            self._unsub_device()
            self._unsub_device = None
        self._visonic_device = None
        await super().async_will_remove_from_hass()

    def _on_change(self, sensor: AlSensorDevice, condition: AlSensorCondition) -> None:
        """Write state updates on sensor change."""
        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if the underlying zone sensor is enrolled."""
        return self._visonic_device is not None and self._visonic_device.isEnrolled()

    @property
    def is_on(self) -> bool | None:
        """Return True if tamper or low battery is active."""
        if self._visonic_device is None:
            return None
        if self._kind == "tamper":
            tamper = self._visonic_device.isTamper()
            zone_tamper = self._visonic_device.isZoneTamper()
            return bool(tamper) or bool(zone_tamper)
        return bool(self._visonic_device.isLowBattery())
