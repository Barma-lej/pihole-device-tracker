"""API client for Pi-hole v6.0+."""

import logging
from typing import Any, Dict, Optional
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)


class PiholeAPIClient:
    """Client for Pi-hole v6.0+ API with FTL authentication."""

    def __init__(self, host: str, password: str = "", timeout: int = 10):
        """Initialize the API client.
        
        Args:
            host: Pi-hole host (IP or hostname)
            password: Web interface password
            timeout: Request timeout in seconds
        """
        self.host = self._normalize_host(host)
        self.password = password
        self.timeout = timeout
        self._sid: Optional[str] = None

    @staticmethod
    def _normalize_host(host: str) -> str:
        """Normalize host URL."""
        host = host.replace("https://", "").replace("http://", "").strip()
        if host.endswith("/"):
            host = host[:-1]
        return host

    async def authenticate(self) -> bool:
        """Authenticate and get session ID.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"http://{self.host}/api/auth"
            payload = {"password": self.password}
            
            _LOGGER.debug(f"Authenticating with Pi-hole at {self.host}")
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._sid = data.get("session", {}).get("sid")
                        if self._sid:
                            _LOGGER.debug(f"✓ Authenticated with Pi-hole")
                            return True
                    elif resp.status == 401:
                        _LOGGER.error("Authentication failed - invalid password")
                    else:
                        _LOGGER.error(f"Auth failed with status {resp.status}")
            
            return False
            
        except asyncio.TimeoutError:
            _LOGGER.error("Authentication timeout")
            return False
        except Exception as err:
            _LOGGER.error(f"Authentication error: {err}")
            return False

    async def get_devices(self) -> Dict[str, Any]:
        """Get network devices from Pi-hole.
        
        Returns:
            Dictionary with device data
        """
        try:
            if not self._sid:
                if not await self.authenticate():
                    return {}
            
            url = f"http://{self.host}/api/network/devices"
            headers = {"X-FTL-SID": self._sid}
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        _LOGGER.debug(f"✓ Got devices from Pi-hole")
                        return data
                    elif resp.status == 401:
                        _LOGGER.warning("Session expired, re-authenticating")
                        self._sid = None
                        return await self.get_devices()  # Retry
                    else:
                        _LOGGER.error(f"get_devices failed: HTTP {resp.status}")
                        return {}
            
        except asyncio.TimeoutError:
            _LOGGER.error("get_devices timeout")
            return {}
        except Exception as err:
            _LOGGER.error(f"get_devices error: {err}")
            return {}

    async def get_dhcp_leases(self) -> Dict[str, Any]:
        """Get DHCP leases from Pi-hole.
        
        Returns:
            Dictionary with DHCP lease data
        """
        try:
            if not self._sid:
                if not await self.authenticate():
                    return {}
            
            url = f"http://{self.host}/api/dhcp/leases"
            headers = {"X-FTL-SID": self._sid}
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        _LOGGER.debug(f"✓ Got DHCP leases from Pi-hole")
                        return data
                    elif resp.status == 401:
                        _LOGGER.warning("Session expired, re-authenticating")
                        self._sid = None
                        return await self.get_dhcp_leases()  # Retry
                    else:
                        _LOGGER.error(f"get_dhcp_leases failed: HTTP {resp.status}")
                        return {}
            
        except asyncio.TimeoutError:
            _LOGGER.error("get_dhcp_leases timeout")
            return {}
        except Exception as err:
            _LOGGER.error(f"get_dhcp_leases error: {err}")
            return {}

    async def test_connection(self) -> bool:
        """Test connection to Pi-hole.
        
        Returns:
            True if connection successful
        """
        try:
            _LOGGER.info(f"Testing connection to Pi-hole at {self.host}")
            result = await self.authenticate()
            if result:
                _LOGGER.info("✓ Connection to Pi-hole successful")
            return result
        except Exception as err:
            _LOGGER.error(f"Connection test failed: {err}")
            return False
