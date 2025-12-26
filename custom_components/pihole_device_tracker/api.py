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
        self.host = host
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def async_get_devices(self) -> Dict[str, Any]:
        """Get list of devices from Pi-hole.
        
        Returns:
            Dictionary containing device information
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.host}{PIHOLE_API_PATH}/clients"
                
                params = {}
                if self.api_key:
                    params["token"] = self.api_key

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        LOGGER.error(f"Pi-hole API returned status {resp.status}")
                        return {}
        except asyncio.TimeoutError:
            LOGGER.error("Timeout connecting to Pi-hole")
            return {}
        except aiohttp.ClientError as err:
            LOGGER.error(f"Error connecting to Pi-hole: {err}")
            return {}
        except Exception as err:
            LOGGER.error(f"Unexpected error: {err}")
            return {}

    async def async_get_status(self) -> Dict[str, Any]:
        """Get Pi-hole status.
        
        Returns:
            Dictionary containing status information
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"http://{self.host}{PIHOLE_API_PATH}/status"
                
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    return {}
        except Exception as err:
            LOGGER.error(f"Error getting Pi-hole status: {err}")
            return {}

    async def async_test_connection(self) -> bool:
        """Test connection to Pi-hole.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            status = await self.async_get_status()
            return bool(status)
        except Exception:
            return False
