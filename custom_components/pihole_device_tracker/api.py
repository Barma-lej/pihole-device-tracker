"""API client for Pi-hole Device Tracker."""

import aiohttp
import asyncio
import logging
import json
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)


class PiholeAPIClient:
    """Client for interacting with Pi-hole API v6.0+.
    
    Pi-hole v6.0+ uses FTL API with session-based authentication (SID).
    No API key needed - just the web password.
    """

    def __init__(
        self,
        host: str,
        password: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        """Initialize the API client.
        
        Args:
            host: Pi-hole host IP address or hostname
            password: Web interface password (NOT API token)
            timeout: Request timeout in seconds
        """
        self.host = self._normalize_host(host)
        self.password = password or ""
        self.timeout = timeout
        self._sid: Optional[str] = None

    @staticmethod
    def _normalize_host(host: str) -> str:
        """Normalize host URL."""
        host = host.replace("https://", "").replace("http://", "")
        host = host.rstrip("/")
        if ":" in host:
            host = host.split(":")[0]
        return host

    async def _async_authenticate(self) -> Optional[str]:
        """Authenticate with Pi-hole and get session ID (SID).
        
        Returns:
            Session ID (SID) if successful, None otherwise
        """
        try:
            if self._sid:
                # Use cached SID
                return self._sid
            
            url = f"http://{self.host}/api/auth"
            payload = {"password": self.password}
            headers = {"Content-Type": "application/json"}
            
            LOGGER.debug(f"Authenticating with Pi-hole at {self.host}")
            
            timeout = aiohttp.ClientTimeout(total=5, connect=3)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url, 
                    json=payload, 
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._sid = data.get("session", {}).get("sid")
                        if self._sid:
                            LOGGER.debug(f"✓ Successfully authenticated with Pi-hole")
                            return self._sid
                        else:
                            LOGGER.error("No SID returned from authentication")
                            return None
                    elif resp.status == 401:
                        LOGGER.error("Authentication failed - wrong password")
                        return None
                    else:
                        text = await resp.text()
                        LOGGER.error(f"Authentication error (HTTP {resp.status}): {text}")
                        return None
                        
        except asyncio.TimeoutError:
            LOGGER.error("Timeout during authentication")
            return None
        except Exception as err:
            LOGGER.error(f"Authentication error: {err}")
            return None

    async def async_get_status(self) -> Dict[str, Any]:
        """Get Pi-hole overall status.
        
        Returns:
            Dictionary containing status information including blocking status
        """
        try:
            # Get session ID
            sid = await self._async_authenticate()
            if not sid:
                return {"status": "error", "reason": "authentication_failed"}
            
            # Get DNS blocking status
            url = f"http://{self.host}/api/dns/blocking"
            headers = {"X-FTL-SID": sid}
            
            LOGGER.debug(f"Getting Pi-hole status from: {url}")
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"✓ Successfully retrieved Pi-hole status")
                        return {"status": "success", "blocking": data.get("blocking", False)}
                    elif resp.status == 401:
                        LOGGER.error("Unauthorized - re-authenticate required")
                        self._sid = None  # Clear cache
                        return await self.async_get_status()  # Retry
                    else:
                        text = await resp.text()
                        LOGGER.error(f"Pi-hole returned HTTP {resp.status}: {text}")
                        return {"status": "error", "code": resp.status}
                        
        except asyncio.TimeoutError:
            LOGGER.error("Timeout getting Pi-hole status")
            return {"status": "error", "reason": "timeout"}
        except Exception as err:
            LOGGER.error(f"Unexpected error getting status: {err}")
            return {"status": "error", "reason": "unknown_error"}

    async def async_get_summary(self) -> Dict[str, Any]:
        """Get Pi-hole summary statistics.
        
        Returns:
            Dictionary with DNS query statistics
        """
        try:
            sid = await self._async_authenticate()
            if not sid:
                return {}
            
            url = f"http://{self.host}/api/stats/summary"
            headers = {"X-FTL-SID": sid}
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"✓ Successfully retrieved summary")
                        return data
                    elif resp.status == 401:
                        self._sid = None
                        return await self.async_get_summary()  # Retry
                    else:
                        LOGGER.error(f"Summary returned HTTP {resp.status}")
                        return {}
                        
        except Exception as err:
            LOGGER.error(f"Error getting summary: {err}")
            return {}

    async def async_get_clients(self) -> Dict[str, Any]:
        """Get list of connected clients.
        
        Returns:
            Dictionary containing client information
        """
        try:
            sid = await self._async_authenticate()
            if not sid:
                return {}
            
            # Get top clients
            url = f"http://{self.host}/api/stats/clients?count=20"
            headers = {"X-FTL-SID": sid}
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"✓ Successfully retrieved clients")
                        return data
                    elif resp.status == 401:
                        self._sid = None
                        return await self.async_get_clients()  # Retry
                    else:
                        return {}
                        
        except Exception as err:
            LOGGER.error(f"Error getting clients: {err}")
            return {}

    async def async_test_connection(self) -> bool:
        """Test connection to Pi-hole.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            LOGGER.info(f"Testing connection to Pi-hole at {self.host}...")
            
            # Try to authenticate
            sid = await self._async_authenticate()
            
            if sid:
                LOGGER.info(f"✓ Connection to Pi-hole successful!")
                return True
            else:
                LOGGER.warning(f"✗ Connection to Pi-hole failed - authentication error")
                return False
            
        except Exception as err:
            LOGGER.error(f"Connection test failed: {err}")
            return False
