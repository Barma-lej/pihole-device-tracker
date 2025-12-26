"""Pi-hole Device Tracker integration for Home Assistant."""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORMS_LIST: Final = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pi-hole Device Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store the config entry data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": None,
        "unsub_update_listener": None,
    }
    
    # Forward the setup to the device tracker platform
    # Use await to properly handle platform loading
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS_LIST)
    
    _LOGGER.debug(f"Set up entry {entry.entry_id} for {entry.title}")
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS_LIST)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok