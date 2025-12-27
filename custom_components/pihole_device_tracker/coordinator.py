from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import AUTH_ENDPOINT, LEASES_ENDPOINT, DEVICES_ENDPOINT

_LOGGER = logging.getLogger(__name__)


class PiholeUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator for Pi-hole v6 with authentication."""

    def __init__(
        self, 
        hass: HomeAssistant, 
        host: str, 
        password: str,
        scan_interval: int
    ):
        self._host = host.rstrip("/")
        self._password = password
        self._session = async_get_clientsession(hass)
        self._sid: Optional[str] = None  # session ID
        
        super().__init__(
            hass,
            _LOGGER,
            name="Pi-hole Device Tracker", 
            update_interval=timedelta(seconds=scan_interval)
        )
    
    async def _authenticate(self) -> bool:
        """Authenticate with Pi-hole v6 and get SID."""
        try:
            auth_url = f"{self._host}{AUTH_ENDPOINT}"
            payload = {"password": self._password}
            
            async with self._session.post(auth_url, json=payload, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._sid = data.get("session", {}).get("sid")
                    if self._sid:
                        _LOGGER.debug("✓ Authenticated with Pi-hole")
                        return True
                    else:
                        _LOGGER.error("No SID in response")
                        return False
                elif resp.status == 401:
                    _LOGGER.error("Authentication failed - wrong password")
                    return False
                else:
                    _LOGGER.error(f"Auth failed: HTTP {resp.status}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Authentication error: {err}")
            return False
    
    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Pi-hole v6."""
        
        # Authenticate if no SID
        if not self._sid:
            if not await self._authenticate():
                raise UpdateFailed("Authentication failed")
        
        leases_url = f"{self._host}{LEASES_ENDPOINT}"
        devices_url = f"{self._host}{DEVICES_ENDPOINT}"
        
        # Add authentication header
        headers = {"X-FTL-SID": self._sid}
        
        try:
            async with self._session.get(leases_url, headers=headers, timeout=10) as resp:
                if resp.status == 401:
                    # Session expired, re-authenticate
                    _LOGGER.warning("Session expired, re-authenticating")
                    self._sid = None
                    return await self._async_update_data()  # Retry
                
                leases_json = await resp.json(content_type=None)
            
            async with self._session.get(devices_url, headers=headers, timeout=10) as resp:
                if resp.status == 401:
                    self._sid = None
                    return await self._async_update_data()  # Retry
                
                devices_json = await resp.json(content_type=None)
                
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(err) from err
        
        # Process data (same as pihole_presence)
        leases = leases_json.get("leases", [])
        devices = devices_json.get("devices", [])
        
        merged: Dict[str, Dict[str, Any]] = {}
        
        for lease in leases:
            mac = lease.get("hwaddr", "").lower()
            if not mac:
                continue
            entry = merged.setdefault(mac, {"ips": set()})
            entry["ips"].add(lease.get("ip"))
            if lease.get("name") and lease["name"] != "*":
                entry["name"] = lease["name"]
            entry["dhcp_expires"] = lease.get("expires")
        
        for dev in devices:
            mac = dev.get("hwaddr", "").lower()
            if not mac:
                continue
            entry = merged.setdefault(mac, {"ips": set()})
            entry.update({
                "interface": dev.get("interface"),
                "first_seen": dev.get("firstSeen"),
                "last_query": dev.get("lastQuery"),
                "num_queries": dev.get("numQueries"),
                "mac_vendor": dev.get("macVendor"),
            })
            for ip_entry in dev.get("ips", []):
                if ip := ip_entry.get("ip"):
                    entry["ips"].add(ip)
                if not entry.get("name") and (n := ip_entry.get("name")) and n != "*":
                    entry["name"] = n
        
        for info in merged.values():
            info["ips"] = ", ".join(sorted(info.get("ips", [])))
        
        return merged
