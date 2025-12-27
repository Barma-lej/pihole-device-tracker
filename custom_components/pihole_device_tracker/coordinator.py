from __future__ import annotations

import asyncio
import logging
import re
import asyncssh
from datetime import timedelta
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    AUTH_ENDPOINT,
    DEVICES_ENDPOINT,
    LEASES_ENDPOINT,
    CONF_AWAY_TIME,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SSH_HOST,
    CONF_SSH_PASSWORD,
    CONF_SSH_PORT,
    CONF_SSH_USERNAME,
    CONF_SSH_KEY_PATH,
    DEFAULT_AWAY_TIME,
    DEFAULT_HOST,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSH_PORT,
    DEFAULT_SSH_USERNAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

class PiholeUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator for Pi-hole v6 with ARP monitoring via SSH."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        password: str,
        scan_interval: int,
        ssh_host: str = None,
        ssh_port: int = DEFAULT_SSH_PORT,
        ssh_username: str = DEFAULT_SSH_USERNAME,
        ssh_password: str = None,
        ssh_key_path: str = None,
    ):
        self._host = self._normalize_host(host)
        self._password = password
        self._scan_interval = scan_interval

        # SSH configuration
        self._ssh_config = {
            "host": ssh_host,
            "port": ssh_port,
            "username": ssh_username,
            "password": ssh_password,
            "key_path": ssh_key_path,
        }

        self._session = async_get_clientsession(hass)
        self._sid: Optional[str] = None
        self._arp_cache: Dict[str, str] = {}  # IP -> MAC

        super().__init__(
            hass,
            _LOGGER,
            name="Pi-hole Device Tracker",
            update_interval=timedelta(seconds=scan_interval),
        )

    @staticmethod
    def _normalize_host(host: str) -> str:
        """Normalize host URL."""
        host = host.replace("https://", "").replace("http://", "").strip()
        if host.endswith("/"):
            host = host[:-1]
        if not host.startswith("http://") and not host.startswith("https://"):
            host = "http://" + host
        return host

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

    async def _get_arp_table(self) -> Dict[str, str]:
        """Получить ARP-таблицу с Pi-hole сервера по SSH."""
        if not self._ssh_config.get("host"):
            return {}

        ssh_config = self._ssh_config
        cmd = "arp -n"

        try:
            connect_kwargs = {
                "host": ssh_config["host"],
                "port": ssh_config["port"],
                "username": ssh_config["username"],
            }

            if ssh_config.get("password"):
                connect_kwargs["password"] = ssh_config["password"]
            elif ssh_config.get("key_path"):
                connect_kwargs["client_keys"] = ssh_config["key_path"]

            async with asyncssh.connect(**connect_kwargs) as conn:
                result = await conn.run(cmd)
                arp_output = result.stdout

            arp_map: Dict[str, str] = {}
            for line in arp_output.strip().split("\n"):
                if line.startswith("Address") or "incomplete" in line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    ip = parts[0]
                    mac = None
                    for part in parts:
                        if re.match(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", part):
                            mac = part
                            break
                    if mac:
                        mac_normalized = mac.lower().replace("-", ":")
                        arp_map[ip] = mac_normalized

            _LOGGER.debug(f"ARP таблица получена: {len(arp_map)} записей")
            return arp_map

        except Exception as err:
            _LOGGER.warning(f"Не удалось получить ARP-таблицу: {err}")
            return {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Pi-hole v6 and merge ARP table."""
        # Authenticate if no SID
        if not self._sid:
            if not await self._authenticate():
                raise UpdateFailed("Authentication failed")

        leases_url = f"{self._host}{LEASES_ENDPOINT}"
        devices_url = f"{self._host}{DEVICES_ENDPOINT}"

        headers = {"X-FTL-SID": self._sid}

        try:
            async with self._session.get(leases_url, headers=headers, timeout=10) as resp:
                if resp.status == 401:
                    _LOGGER.warning("Session expired, re-authenticating")
                    self._sid = None
                    return await self._async_update_data()
                leases_json = await resp.json(content_type=None)

            async with self._session.get(devices_url, headers=headers, timeout=10) as resp:
                if resp.status == 401:
                    self._sid = None
                    return await self._async_update_data()
                devices_json = await resp.json(content_type=None)

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(err) from err

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
            entry.update(
                {
                    "interface": dev.get("interface"),
                    "first_seen": dev.get("firstSeen"),
                    "last_query": dev.get("lastQuery"),
                    "num_queries": dev.get("numQueries"),
                    "mac_vendor": dev.get("macVendor"),
                }
            )
            for ip_entry in dev.get("ips", []):
                if ip := ip_entry.get("ip"):
                    entry["ips"].add(ip)
                if not entry.get("name") and (n := ip_entry.get("name")) and n != "*":
                    entry["name"] = n

        for info in merged.values():
            info["ips"] = ", ".join(sorted(info.get("ips", [])))

        # Merge ARP data
        self._arp_cache = await self._get_arp_table()
        for mac, info in merged.items():
            ips = info.get("ips", [])
            if isinstance(ips, str):
                ips = [ips]
            for ip, arp_mac in self._arp_cache.items():
                if arp_mac.replace(":", "-").lower() == mac.replace(":", "-").lower():
                    if ip not in ips:
                        ips.append(ip)
                    info["ips"] = ips
                    info["arp_ip"] = ip
                    break

        return merged
