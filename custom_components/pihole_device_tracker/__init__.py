"""Pi-hole Device Tracker integration."""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__name__)

PLATFORMS: Final = [Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pi-hole Device Tracker from a config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    
    _LOGGER.debug(f"Setting up {DOMAIN} entry for {entry.title}")
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Listen for unload
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    
    _LOGGER.debug(f"Unloading {DOMAIN} entry for {entry.title}")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)