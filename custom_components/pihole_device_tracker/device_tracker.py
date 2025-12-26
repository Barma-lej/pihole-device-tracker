"""Device tracker for Pi-hole."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from homeassistant.components.device_tracker import SOURCE_TYPE_ROUTER
from homeassistant.components.device_tracker.device_tracker_entity import DeviceTrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import PiholeAPIClient
from .const import (
    CONF_CONSIDER_AWAY,
    CONF_POLL_INTERVAL,
    DEFAULT_CONSIDER_AWAY,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker from config entry."""
    
    host = config_entry.data.get(CONF_HOST)
    password = config_entry.data.get(CONF_PASSWORD, "")
    poll_interval = config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    consider_away = config_entry.data.get(CONF_CONSIDER_AWAY, DEFAULT_CONSIDER_AWAY)
    
    _LOGGER.debug(f"Setting up device tracker for {host}")
    
    # Create API client
    client = PiholeAPIClient(host=host, password=password)
    
    # Create coordinator for periodic updates
    coordinator = PiholeCoordinator(
        hass=hass,
        client=client,
        poll_interval=poll_interval,
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    hass.data[DOMAIN][config_entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
        "consider_away": consider_away,
    }
    
    # Create device tracker entity
    entities = [
        PiholePresenceTracker(
            coordinator=coordinator,
            config_entry=config_entry,
            consider_away=consider_away,
        )
    ]
    
    async_add_entities(entities)
    
    _LOGGER.debug(f"Device tracker set up for {host}")


class PiholeCoordinator(DataUpdateCoordinator):
    """Coordinator for Pi-hole device tracking."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        client: PiholeAPIClient,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ):
        """Initialize coordinator."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Pi-hole Device Tracker",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.client = client
        self.devices: Dict[str, Dict[str, Any]] = {}
    
    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Pi-hole."""
        try:
            _LOGGER.debug("Fetching devices from Pi-hole")
            
            # Fetch devices and DHCP info
            devices = await self.client.get_devices()
            dhcp = await self.client.get_dhcp_leases()
            
            # Process devices
            processed_devices = {}
            
            if isinstance(devices, dict):
                for device_id, device_info in devices.items():
                    if isinstance(device_info, dict):
                        mac = device_info.get("hwaddr", device_id)
                        processed_devices[mac] = {
                            "hostname": device_info.get("name", "Unknown"),
                            "ips": device_info.get("ipaddrs", []),
                            "last_query": device_info.get("lastquery", 0),
                            "first_seen": device_info.get("firstseen", 0),
                        }
            
            self.devices = processed_devices
            _LOGGER.debug(f"Updated {len(processed_devices)} devices")
            
            return {
                "devices": processed_devices,
                "dhcp": dhcp if isinstance(dhcp, dict) else {},
            }
            
        except Exception as err:
            _LOGGER.error(f"Error fetching data: {err}")
            raise UpdateFailed(f"Error communicating with Pi-hole: {err}")


class PiholePresenceTracker(CoordinatorEntity, DeviceTrackerEntity):
    """Device tracker for Pi-hole presence."""
    
    _attr_name = "Presence via Pi-hole"
    _attr_unique_id = "pihole_presence_tracker"
    _attr_source_type = SOURCE_TYPE_ROUTER
    
    def __init__(
        self,
        coordinator: PiholeCoordinator,
        config_entry: ConfigEntry,
        consider_away: int = DEFAULT_CONSIDER_AWAY,
    ):
        """Initialize device tracker."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.consider_away = consider_away
        self._attr_device_name = f"Pi-hole ({config_entry.data.get(CONF_HOST)})"
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
    
    async def async_update(self) -> None:
        """Update device tracker."""
        await self.coordinator.async_request_refresh()
    
    def __init__(self, coordinator, config_entry, consider_away=DEFAULT_CONSIDER_AWAY):
        """Initialize."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self.consider_away = consider_away
        self._tracked_devices: Dict[str, str] = {}
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_write_ha_state()
