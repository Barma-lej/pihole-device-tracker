"""Device tracker for Pi-hole."""

import logging
from typing import Any, Dict

from homeassistant.components.device_tracker import DeviceScanner
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant

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
    
    # Create scanner
    scanner = PiholeDeviceScanner(
        hass=hass,
        client=client,
        scan_interval=scan_interval,
    )
    
    # Store scanner in hass data for later access
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": client,
        "scanner": scanner,
    }
    
    # Add device tracker entity
    async_add_entities([scanner])
    
    _LOGGER.debug(f"Device tracker set up for {host}")


class PiholeDeviceScanner(DeviceScanner):
    """Device scanner for Pi-hole."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        client: PiholeAPIClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize device scanner."""
        self.hass = hass
        self.client = client
        self.scan_interval = scan_interval
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._name = f"Pi-hole Device Tracker ({client.host})"
    
    @property
    def name(self) -> str:
        """Return the name of the device scanner."""
        return self._name
    
    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{DOMAIN}_{self.client.host}"
    
    async def async_update(self) -> None:
        """Update device list from Pi-hole."""
        try:
            # Get status
            status = await self.client.async_get_status()
            
            if status.get("status") == "success":
                _LOGGER.debug(f"Pi-hole status: Blocking is {'enabled' if status.get('blocking') else 'disabled'}")
            else:
                _LOGGER.error(f"Failed to get Pi-hole status: {status}")
            
            # Get clients/devices
            clients = await self.client.async_get_clients()
            if clients:
                self._devices = clients
                _LOGGER.debug(f"Updated {len(clients)} devices from Pi-hole")
            
        except Exception as err:
            _LOGGER.error(f"Error updating device list: {err}")
    
    async def async_see(self, **kwargs) -> None:
        """Mark a device as seen."""
        pass
    
    @property
    def devices(self) -> Dict[str, Dict[str, Any]]:
        """Return the devices."""
        return self._devices
