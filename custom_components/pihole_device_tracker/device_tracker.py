"""Device tracker platform for Pi-hole."""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.components.device_tracker import PLATFORM_SCHEMA, DeviceScanner
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .api import PiholeAPIClient
from .const import CONF_API_KEY, CONF_INTERVAL, DEFAULT_INTERVAL

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({})


async def async_get_scanner(
    hass: HomeAssistant, config: ConfigType
) -> Optional[DeviceScanner]:
    """Return a device scanner."""
    return PiholeDeviceScanner(hass, config)


class PiholeDeviceScanner(DeviceScanner):
    """Scanner for Pi-hole devices."""

    def __init__(self, hass: HomeAssistant, config: ConfigType) -> None:
        """Initialize the scanner."""
        self.hass = hass
        self.client = PiholeAPIClient(
            host=config.get(CONF_HOST),
            api_key=config.get(CONF_API_KEY),
        )
        self.last_results: Dict[str, Dict[str, Any]] = {}
        self.update_interval = timedelta(
            seconds=config.get(CONF_INTERVAL, DEFAULT_INTERVAL)
        )

    async def async_scan_devices(self) -> list[str]:
        """Return list of device MACs."""
        devices = await self.client.async_get_devices()
        return [d.get("mac") for d in devices.get("clients", []) if d.get("mac")]

    async def async_get_device_name(self, device: str) -> Optional[str]:
        """Return the name of a device."""
        devices = await self.client.async_get_devices()
        for d in devices.get("clients", []):
            if d.get("mac") == device:
                return d.get("name") or d.get("ip")
        return None

    def get_extra_attributes(self, device: str) -> Dict[str, Any]:
        """Return extra attributes for a device."""
        if device in self.last_results:
            return self.last_results[device]
        return {}
