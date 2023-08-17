"""Platform for recording current irrigation zone status"""
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.util import slugify
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_platform
from homeassistant.const import (
    CONF_NAME,
    )
from .const import (
    ATTR_ZONES,
    ATTR_ZONE
    )

_LOGGER = logging.getLogger(__name__)

async def _async_create_entities(hass: HomeAssistant, config, unique_id):

    sensors = []
    #append multiple sensors
    for zone in config.get(ATTR_ZONES):
        sensors.append(
            ZoneStatus(
                hass,
                config.get(CONF_NAME),
                zone.get(ATTR_ZONE).split(".")[1],
                unique_id
            )
        )
    return sensors

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Initialize config entry. form config flow"""
    unique_id = config_entry.entry_id
    if config_entry.options != {}:
        config = config_entry.options
    else:
        config = config_entry.data

    async_add_entities(await _async_create_entities(hass, config, unique_id))

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        "set_zone_status",
        {
            vol.Required('status'): str,
        },
        "set_zone_status",
    )

class ZoneStatus(SensorEntity):
    ''' Rain factor class defn'''

    def __init__(
        self,
        hass: HomeAssistant,
        program,
        zone,
        unique_id
    ) -> None:

        self._state          = 'off'
        self._attr_unique_id = slugify(f'{unique_id}_{zone}_status')
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_has_entity_name = True
        self._attr_name = slugify(f'{program}_{zone}_status')
        self._attr_should_poll = False
        self._attr_translation_key = 'zonestatus'

    async def set_zone_status(self, status='off'):
        '''function to set the runtime state value'''
        self._state = status
        self.async_schedule_update_ha_state()

    @property
    def options(self):
        """Return the sensor state options"""
        return  [
            'on'
           ,'off'
           ,'pending'
           ,'eco'
           ,'disabled']

    @property
    def native_value(self):
        """Return the state."""
        return self._state
