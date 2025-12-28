"""Pi-hole update coordinator with ARP monitoring via SSH."""
import logging
import re
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.shell_command import async_service_call_from_config
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

        self._ssh_config = {
            "host": ssh_host,
            "port": ssh_port,
            "username": ssh_username,
            "password": ssh_password,
        }

        self._session = async_get_clientsession(hass)
        self._arp_cache: Dict[str, str] = {}
        self._hass = hass

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
        devices_url = f"{self._host}/api/network/devices?max_devices=999&max_addresses=24"
        
        try:
            async with self._session.get(devices_url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {})
                elif response.status == 401:
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
        """Получить ARP-таблицу с Pi-hole сервера."""
        if not self._ssh_config.get("host"):
            return {}

        ssh_config = self._ssh_config

        # Формируем SSH команду
        ssh_cmd = (
            f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "
            f"-p {ssh_config['port']} {ssh_config['username']}@{ssh_config['host']} 'arp -n'"
        )

        try:
            # Выполняем через shell_command (если настроено)
            response = await self._hass.services.async_call(
                "shell_command",
                "get_arp_pi",
                blocking=True,
                timeout=30
            )
            
            # Получаем результат из контекста (недоступно напрямую)
            # Поэтому используем asyncio.create_subprocess_exec
            raise Exception("Используем subprocess")
            
        except Exception:
            # Запасной вариант - напрямую через subprocess
            import asyncio
            
            cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p {ssh_config['port']} {ssh_config['username']}@{ssh_config['host']} 'arp -n'"
            
            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                _LOGGER.warning(f"SSH ошибка: {stderr.decode()}")
                return {}
            
            arp_output = stdout.decode()

            # Парсим вывод
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

    async def _async_update_data(self) -> Dict[str, Any]:
        """Обновить данные с Pi-hole API и ARP-таблицы."""
        devices = await self._get_devices()
        self._arp_cache = await self._get_arp_table()

        data: Dict[str, Any] = {}
        
        for mac, info in devices.items():
            mac_normalized = mac.lower().replace("-", ":")
            
            arp_ip = None
            for ip, arp_mac in self._arp_cache.items():
                if arp_mac == mac_normalized:
                    arp_ip = ip
                    break

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