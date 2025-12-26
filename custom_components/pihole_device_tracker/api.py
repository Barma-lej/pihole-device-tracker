"""API client for Pi-hole Device Tracker."""

import aiohttp
import asyncio
import logging
from typing import Any, Dict, Optional
from .const import API_TIMEOUT, PIHOLE_API_PATH

LOGGER = logging.getLogger(__name__)


class PiholeAPIClient:
    """Client for interacting with Pi-hole API."""

    def __init__(
        self,
        host: str,
        api_key: Optional[str] = None,
        timeout: int = API_TIMEOUT,
    ) -> None:
        """Initialize the API client.
        
        Args:
            host: Pi-hole host (IP or hostname)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.host = self._normalize_host(host)
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    @staticmethod
    def _normalize_host(host: str) -> str:
        """Normalize host URL.
        
        Remove protocol if present and ensure it's just the host.
        """
        # Remove http:// or https:// if present
        host = host.replace("https://", "").replace("http://", "")
        # Remove trailing slashes
        host = host.rstrip("/")
        return host

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint."""
        return f"http://{self.host}/api/{endpoint}"

    async def async_get_devices(self) -> Dict[str, Any]:
        """Get list of devices from Pi-hole.
        
        Returns:
            Dictionary containing device information
        """
        try:
            url = self._build_url("clients")
            
            params = {}
            if self.api_key:
                params["token"] = self.api_key

            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"Successfully retrieved devices from Pi-hole")
                        return data
                    else:
                        LOGGER.error(f"Pi-hole API returned status {resp.status}")
                        return {}
                        
        except asyncio.TimeoutError as err:
            LOGGER.error(f"Timeout connecting to Pi-hole at {self.host}: {err}")
            return {}
        except aiohttp.ClientConnectorError as err:
            LOGGER.error(f"Connection error to Pi-hole at {self.host}: {err}")
            return {}
        except aiohttp.ClientError as err:
            LOGGER.error(f"Client error connecting to Pi-hole: {err}")
            return {}
        except Exception as err:
            LOGGER.error(f"Unexpected error getting devices: {err}")
            return {}

    async def async_get_status(self) -> Dict[str, Any]:
        """Get Pi-hole status.
        
        Returns:
            Dictionary containing status information
        """
        try:
            url = self._build_url("status")
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"Successfully retrieved status from Pi-hole")
                        return data
                    else:
                        LOGGER.error(f"Pi-hole status returned {resp.status}")
                        return {}
                        
        except asyncio.TimeoutError as err:
            LOGGER.error(f"Timeout getting Pi-hole status: {err}")
            return {}
        except aiohttp.ClientError as err:
            LOGGER.error(f"Error getting Pi-hole status: {err}")
            return {}
        except Exception as err:
            LOGGER.error(f"Unexpected error getting status: {err}")
            return {}

    async def async_test_connection(self) -> bool:
        """Test connection to Pi-hole.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            LOGGER.debug(f"Testing connection to Pi-hole at {self.host}")
            status = await self.async_get_status()
            is_connected = bool(status)
            LOGGER.info(f"Pi-hole connection test: {'SUCCESS' if is_connected else 'FAILED'}")
            return is_connected
        except Exception as err:
            LOGGER.error(f"Connection test failed: {err}")
            return False
