''' __init__'''
from __future__ import annotations
from ctypes.wintypes import BOOL
import logging
from homeassistant.util import slugify
import asyncio
from . import utils
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    SERVICE_TURN_OFF,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant,callback
#from homeassistant import config_entries

from .const import (
    DOMAIN,
    SWITCH_ID_FORMAT,
    CONST_SWITCH,
    ATTR_DEVICE_TYPE,
    ATTR_SHOW_CONFIG
    )

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up irrigtest from a config entry."""
    # store an object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = {ATTR_NAME:entry.data.get(ATTR_NAME)}

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(
            entry, Platform.SENSOR
            )
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(
            entry, Platform.BINARY_SENSOR
            )
    )
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(
            entry, Platform.SWITCH
        )
    )
    entry.async_on_unload(entry.add_update_listener(config_entry_update_listener))
    return True

async def config_entry_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener, called when the config entry options are changed."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    #clean up any related helpers

    await hass.config_entries.async_unload_platforms(
        entry, (Platform.SENSOR,)
        )
    await hass.config_entries.async_unload_platforms(
        entry, (Platform.BINARY_SENSOR,)
        )
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, (Platform.SWITCH,)
    ):

        return unload_ok

async def async_setup(hass:HomeAssistant, config):
    '''setup the irrigation'''
    hass.data.setdefault(DOMAIN, {})

    # 1. Serve lovelace card
    path = Path(__file__).parent / "www"
    utils.register_static_path(hass.http.app, "/irrigationprogram/irrigation-card.js", path / "irrigation-card.js")

    # 2. Add card to resources
    version = getattr(hass.data["integrations"][DOMAIN], "version", 0)
    await utils.init_resource(hass, "/irrigationprogram/irrigation-card.js", str(version))


    async def async_stop_programs(call):
        ''' stop all running programs'''

        for data in hass.data[DOMAIN].values():
            if data.get(ATTR_NAME) == call.data.get("ignore", ""):
                await asyncio.sleep(1)
                continue
            device = SWITCH_ID_FORMAT.format(slugify(data.get(ATTR_NAME)))
            servicedata = {ATTR_ENTITY_ID: device}

            #warn if the program is terminated by a service call
            if hass.states.get(device).state == "on":
                if call.data.get("ignore", ""):
                    _LOGGER.warning("Irrigation Program '%s' terminated by '%s'", data.get(ATTR_NAME), call.data.get("ignore", "") )
                else:
                    _LOGGER.warning("Irrigation Program '%s' terminated ", data.get(ATTR_NAME))
                await hass.services.async_call(CONST_SWITCH, SERVICE_TURN_OFF, servicedata)
    # END async_stop_switches

    # register the service
    hass.services.async_register(DOMAIN, "stop_programs", async_stop_programs)

    return True

@callback
def _async_find_matching_config_entry(
    hass: HomeAssistant, name
) -> BOOL:
    '''determine if a config has been imported from YAML'''
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_NAME) == name:
            return True
    return False

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.info("Migrating from version %s", config_entry.version)

    if config_entry.version == 2:
        if config_entry.options == {}:
            new = {**config_entry.data} #config_entry.data
        else:
            new = {**config_entry.options} #config_entry.options
        new.update({ATTR_DEVICE_TYPE: 'generic'})
        new.pop(ATTR_SHOW_CONFIG)
        config_entry.version = 3
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True

