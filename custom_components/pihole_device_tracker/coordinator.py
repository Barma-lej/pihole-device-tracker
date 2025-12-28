"""Pi-hole update coordinator with ARP monitoring via SSH."""
import logging
import re
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEFAULT_SSH_PORT,
    DEFAULT_SSH_USERNAME,
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

        # SSH конфигурация
        self._ssh_config = {
            "host": ssh_host,
            "port": ssh_port,
            "username": ssh_username,
            "password": ssh_password,
            "key_path": ssh_key_path,
        }

        self._session = async_get_clientsession(hass)
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

    async def _authenticate(self) -> Optional[str]:
        """Аутентификация в Pi-hole API и получение SID."""
        auth_url = f"{self._host}/api/auth"
        auth_data = {"password": self._password}
        
        try:
            async with self._session.post(
                auth_url, json=auth_data, timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("session", {}).get("sid")
                return None
        except Exception as err:
            _LOGGER.error(f"Ошибка аутентификации: {err}")
            return None

    async def _get_devices(self) -> Dict[str, Any]:
        """Получить список устройств из Pi-hole API."""
        # Сначала пробуем без аутентификации
        devices_url = f"{self._host}/api/network/devices?max_devices=999&max_addresses=24"
        
        try:
            async with self._session.get(devices_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                elif response.status == 401:
                    # Требуется аутентификация
                    sid = await self._authenticate()
                    if sid:
                        headers = {"Authorization": f"Bearer {sid}"}
                        async with self._session.get(devices_url, headers=headers, timeout=10) as resp:
                            if resp.status == 200:
                                dev_data = await resp.json()
                                return dev_data.get("data", {})
                    _LOGGER.warning("Не удалось аутентифицироваться в Pi-hole")
                    return {}
                else:
                    _LOGGER.error(f"Ошибка получения устройств: {response.status}")
                    return {}
        except Exception as err:
            _LOGGER.error(f"Ошибка запроса к Pi-hole: {err}")
            return {}

    async def _get_arp_table(self) -> Dict[str, str]:
        """Получить ARP-таблицу с Pi-hole сервера по SSH."""
        if not self._ssh_config.get("host"):
            return {}

        ssh_config = self._ssh_config

        # Lazy import
        import asyncssh

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

            # Парсим вывод: IP -> MAC
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
        """Обновить данные с Pi-hole API и ARP-таблицы."""
        # Получаем устройства с Pi-hole
        devices = await self._get_devices()
        
        # Получаем ARP-таблицу
        self._arp_cache = await self._get_arp_table()

        # Объединяем данные
        data: Dict[str, Any] = {}
        
        for mac, info in devices.items():
            # Нормализуем MAC
            mac_normalized = mac.lower().replace("-", ":")
            
            # Ищем IP в ARP таблице
            arp_ip = None
            for ip, arp_mac in self._arp_cache.items():
                if arp_mac == mac_normalized:
                    arp_ip = ip
                    break

            # Обогащаем данные
            if arp_ip:
                ips = info.get("ips", [])
                if isinstance(ips, str):
                    ips = [ips]
                elif not isinstance(ips, list):
                    ips = []
                
                if arp_ip not in ips:
                    ips.append(arp_ip)
                info["ips"] = ips
                info["arp_ip"] = arp_ip
            
            data[mac_normalized] = info

        _LOGGER.debug(f"Устройства получены: {len(data)}")
        return data