"""Device tracker for Pi-hole."""

import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.components.device_tracker import (
    SOURCE_TYPE_ROUTER,
    async_see,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .api import PiholeAPIClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, 
    config_entry: ConfigEntry, 
    async_add_entities: Any,
) -> None:
    """Set up device tracker from config entry."""
    
    host = config_entry.data.get(CONF_HOST)
    password = config_entry.data.get(CONF_PASSWORD, "")
    scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    _LOGGER.debug(f"Setting up device tracker for Pi-hole at {host}")
    
    # Create API client
    client = PiholeAPIClient(
        host=host,
        password=password,
        timeout=10,
    )
    
    # Test connection
    is_connected = await client.async_test_connection()
    if not is_connected:
        _LOGGER.error(f"Failed to connect to Pi-hole at {host}")
        return
    
    # Create tracker
    tracker = PiholeDeviceTracker(
        hass=hass,
        client=client,
        config_entry=config_entry,
        scan_interval=scan_interval,
    )
    
    # Store tracker in hass data for later access
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": client,
        "tracker": tracker,
    }
    
    # Start the tracker
    await tracker.async_added_to_hass()
    
    _LOGGER.debug(f"Device tracker set up for {host}")


class PiholeDeviceTracker:
    """Device tracker for Pi-hole."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        client: PiholeAPIClient,
        config_entry: ConfigEntry,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize device tracker."""
        self.hass = hass
        self.client = client
        self.config_entry = config_entry
        self.scan_interval = scan_interval
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._name = f"Pi-hole ({client.host})"
        self._unsub_update: Optional[Any] = None
    
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        _LOGGER.debug(f"Device tracker added to hass")
        # Start periodic update
        await self._async_update_devices()
        self._schedule_update()
    
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        if self._unsub_update:
            self._unsub_update()
    
    def _schedule_update(self) -> None:
        """Schedule next update."""
        self._unsub_update = async_track_time_interval(
            self.hass,
            self._async_update_devices,
            timedelta(seconds=self.scan_interval),
        )
    
    async def _async_update_devices(self, now: Any = None) -> None:
        """Update devices from Pi-hole."""
        try:
            _LOGGER.debug("Updating devices from Pi-hole")
            
            # Get status
            status = await self.client.async_get_status()
            
            if status.get("status") == "success":
                blocking = status.get("blocking")
                _LOGGER.debug(f"Pi-hole status: Blocking is {'enabled' if blocking else 'disabled'}")
            else:
                _LOGGER.error(f"Failed to get Pi-hole status: {status}")
            
            # Get clients/devices
            clients = await self.client.async_get_clients()
            if isinstance(clients, dict) and clients:
                self._devices = clients
                _LOGGER.debug(f"Updated {len(clients)} devices from Pi-hole")
                
                # Report devices to Home Assistant
                await self._async_see_devices()
            
        except Exception as err:
            _LOGGER.error(f"Error updating device list: {err}")
    
    async def _async_see_devices(self) -> None:
        """Report devices to Home Assistant."""
        for device_id, device_info in self._devices.items():
            try:
                # Extract device information
                if isinstance(device_info, dict):
                    device_name = device_info.get("name", f"Device {device_id}")
                    device_ip = device_info.get("ip", "")
                    device_mac = device_info.get("hwaddr", device_id)
                else:
                    device_name = f"Device {device_id}"
                    device_ip = ""
                    device_mac = device_id
                
                # Report device to Home Assistant
                await async_see(
                    self.hass,
                    mac=device_mac,
                    host_name=device_name,
                    source_type=SOURCE_TYPE_ROUTER,
                    source=DOMAIN,
                    attributes={
                        "ip": device_ip,
                        "host": self.client.host,
                    }
                )
                
            except Exception as err:
                _LOGGER.error(f"Error reporting device {device_id}: {err}")
