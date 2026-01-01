"""Pi-hole update coordinator."""
from __future__ import annotations

import asyncio
import logging
import re
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
    DEFAULT_SSH_PORT,
    DEFAULT_SSH_USERNAME,
)

_LOGGER = logging.getLogger(__name__)


class PiholeUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinator for Pi-hole v6 with authentication and optional ARP monitoring."""

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
    ):
        self._host = self._normalize_host(host)
        self._password = password
        self._session = async_get_clientsession(hass)
        self._sid: Optional[str] = None

        # SSH опционально
        self._ssh_config = {
            "host": ssh_host,
            "port": ssh_port,
            "username": ssh_username,
            "password": ssh_password,
        } if ssh_host else None

        self._arp_cache: Dict[str, str] = {}

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

    def _ssh_get_arp_sync(self, host: str, port: int, username: str, password: str) -> str:
        """Синхронный SSH запрос через asyncio.run()."""
        import asyncssh

        async def ssh_task():
            async with asyncssh.connect(
                host=host,
                port=port,
                username=username,
                password=password,
                known_hosts=None
            ) as conn:
                # Используем ip neigh show nud reachable - только свежие записи!
                result = await conn.run("ip neigh show nud reachable")
                return result.stdout, result.stderr, result.exit_status

        stdout, stderr, exit_status = asyncio.run(ssh_task())
        
        _LOGGER.debug(f"ARP SSH exit_status: {exit_status}")
        _LOGGER.debug(f"ARP SSH stderr: {stderr}")
        
        return stdout

    async def _get_arp_table(self) -> Dict[str, str]:
        """Получить ARP-таблицу (только REACHABLE) через SSH."""
        if not self._ssh_config:
            _LOGGER.debug("ARP: SSH не настроен (опционально)")
            return {}

        ssh_config = self._ssh_config
        _LOGGER.debug(f"ARP: Подключение к {ssh_config['username']}@{ssh_config['host']}")

        try:
            loop = asyncio.get_running_loop()
            stdout = await loop.run_in_executor(
                None,
                self._ssh_get_arp_sync,
                ssh_config["host"],
                ssh_config["port"],
                ssh_config["username"],
                ssh_config["password"],
            )

            _LOGGER.debug(f"ARP raw output:\n{stdout[:1000]}")
            
            arp_map: Dict[str, str] = {}
            count = 0
            for line in stdout.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                
                # Формат: "IP dev IFACE lladdr MAC STATE"
                parts = line.split()
                if len(parts) >= 5:
                    ip = parts[0]
                    # MAC в 4-й позиции
                    mac = None
                    for part in parts:
                        if re.match(r"^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$", part.lower()):
                            mac = part.lower()
                            break
                    
                    if mac:
                        mac_normalized = mac.replace("-", ":")
                        arp_map[ip] = mac_normalized
                        count += 1
                        _LOGGER.debug(f"ARP REACHABLE: {ip} -> {mac_normalized}")

            _LOGGER.debug(f"ARP: Получено {count} REACHABLE записей")
            return arp_map

        except Exception as err:
            _LOGGER.warning(f"ARP: Ошибка получения - {err}")
            return {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Pi-hole v6."""
        if not self._sid:
            if not await self._authenticate():
                raise UpdateFailed("Authentication failed")

        headers = {"X-FTL-SID": self._sid}
        leases_url = f"{self._host}{LEASES_ENDPOINT}"
        devices_url = f"{self._host}{DEVICES_ENDPOINT}"

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

        # Обработка данных
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

        # ARP опционально
        self._arp_cache = await self._get_arp_table()
        if self._arp_cache:
            arp_count = 0
            for mac, info in merged.items():
                for ip, arp_mac in self._arp_cache.items():
                    if arp_mac == mac:
                        if ip not in info["ips"]:
                            info["ips"].add(ip)
                            arp_count += 1
            if arp_count > 0:
                _LOGGER.debug(f"ARP: Обогащено {arp_count} устройств")

        for info in merged.values():
            info["ips"] = ", ".join(sorted(info.get("ips", [])))

        _LOGGER.debug(f"Устройства: {len(merged)}")
        return merged