"""API client for Pi-hole Device Tracker."""

import aiohttp
import asyncio
import logging
from typing import Any, Dict, Optional
from urllib.parse import urlencode

LOGGER = logging.getLogger(__name__)


class PiholeAPIClient:
    """Client for interacting with Pi-hole API v6.0+.
    
    Pi-hole v6.0 uses RESTful /api endpoints instead of /admin/api.php
    """

    def __init__(
        self,
        host: str,
        api_key: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        """Initialize the API client.
        
        Args:
            host: Pi-hole host IP address or hostname
            api_key: Optional API token for authentication
            timeout: Request timeout in seconds
        """
        self.host = self._normalize_host(host)
        self.api_key = api_key
        self.timeout = timeout

    @staticmethod
    def _normalize_host(host: str) -> str:
        """Normalize host URL.
        
        Remove protocol if present and ensure it's just the host.
        """
        # Remove http:// or https:// if present
        host = host.replace("https://", "").replace("http://", "")
        # Remove trailing slashes
        host = host.rstrip("/")
        # Remove port if present (we'll use default 80)
        if ":" in host:
            host = host.split(":")[0]
        return host

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests.
        
        Returns:
            Dictionary of headers including API key if provided
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        # Add API token to header if provided
        if self.api_key:
            headers["X-API-Token"] = self.api_key
        
        return headers

    def _build_url(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Build full URL for Pi-hole API endpoint.
        
        Pi-hole v6.0+ uses /api/endpoint RESTful format
        
        Args:
            endpoint: API endpoint (e.g., "status", "dns/statistics")
            params: Optional query parameters
            
        Returns:
            Full URL string
        """
        url = f"http://{self.host}/api/{endpoint}"
        
        # Add query string if parameters exist
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
        
        return url

    async def async_get_status(self) -> Dict[str, Any]:
        """Get Pi-hole overall status.
        
        Returns:
            Dictionary containing status information
        """
        try:
            # Pi-hole v6.0 status endpoint
            url = self._build_url("status")
            headers = self._get_headers()
            
            LOGGER.debug(f"Getting Pi-hole status from: {url}")
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"✓ Successfully retrieved Pi-hole status")
                        return data
                    elif resp.status == 400:
                        text = await resp.text()
                        LOGGER.error(f"Bad request (400): {text}")
                        return {"status": "error", "code": 400, "message": text}
                    elif resp.status == 401:
                        LOGGER.error(f"Unauthorized (401) - Check API token")
                        return {"status": "error", "code": 401, "message": "Unauthorized"}
                    elif resp.status == 404:
                        LOGGER.error(f"Endpoint not found (404)")
                        return {"status": "error", "code": 404, "message": "Not found"}
                    else:
                        text = await resp.text()
                        LOGGER.error(f"Pi-hole returned HTTP {resp.status}: {text}")
                        return {"status": "error", "code": resp.status, "message": text}
                        
        except asyncio.TimeoutError as err:
            LOGGER.error(f"Timeout getting Pi-hole status: {err}")
            return {"status": "error", "reason": "timeout"}
        except aiohttp.ClientConnectorError as err:
            LOGGER.error(f"Connection error to Pi-hole at {self.host}: {err}")
            return {"status": "error", "reason": "connection_error"}
        except aiohttp.ClientError as err:
            LOGGER.error(f"HTTP client error: {err}")
            return {"status": "error", "reason": "http_error"}
        except Exception as err:
            LOGGER.error(f"Unexpected error getting status: {err}")
            return {"status": "error", "reason": "unknown_error"}

    async def async_get_dns_statistics(self) -> Dict[str, Any]:
        """Get DNS query statistics.
        
        Returns:
            Dictionary containing DNS statistics
        """
        try:
            url = self._build_url("dns/statistics")
            headers = self._get_headers()
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"✓ Successfully retrieved DNS statistics")
                        return data
                    else:
                        LOGGER.error(f"DNS statistics returned HTTP {resp.status}")
                        return {}
                        
        except Exception as err:
            LOGGER.error(f"Error getting DNS statistics: {err}")
            return {}

    async def async_get_summary(self) -> Dict[str, Any]:
        """Get Pi-hole summary statistics.
        
        Returns:
            Dictionary with today's statistics
        """
        try:
            url = self._build_url("summary")
            headers = self._get_headers()
            
            timeout = aiohttp.ClientTimeout(total=self.timeout, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        LOGGER.debug(f"✓ Successfully retrieved summary")
                        return data
                    else:
                        LOGGER.error(f"Summary returned HTTP {resp.status}")
                        return {}
                        
        except Exception as err:
            LOGGER.error(f"Error getting summary: {err}")
            return {}

    async def async_test_connection(self) -> bool:
        """Test connection to Pi-hole.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            LOGGER.info(f"Testing connection to Pi-hole at {self.host}...")
            status = await self.async_get_status()
            
            # Check if we got a valid response (not an error response)
            is_connected = "error" not in status or status.get("code") not in (400, 401, 404)
            
            if is_connected:
                LOGGER.info(f"✓ Connection to Pi-hole successful!")
                return True
            else:
                error_msg = status.get("message", status.get("reason", "unknown error"))
                LOGGER.warning(f"✗ Connection to Pi-hole failed: {error_msg}")
                return False
            
        except Exception as err:
            LOGGER.error(f"Connection test failed: {err}")
            return False
