"""Pi-hole update coordinator with ARP monitoring via SSH."""
import logging
import re
from datetime import timedelta
from typing import Any, Dict, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    # CONF_AWAY_TIME,
    # CONF_PASSWORD,
    # CONF_SCAN_INTERVAL,
    # CONF_SSH_HOST,
    # CONF_SSH_PASSWORD,
    # CONF_SSH_PORT,
    # CONF_SSH_USERNAME,
    # CONF_SSH_KEY_PATH,
    # DEFAULT_AWAY_TIME,
    # DEFAULT_HOST,
    # DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSH_PORT,
    DEFAULT_SSH_USERNAME,
    # DOMAIN,
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
        self._sid: Optional[str] = None
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

    async def _get_arp_table(self) -> Dict[str, str]:
        """Получить ARP-таблицу с Pi-hole сервера по SSH."""
        if not self._ssh_config.get("host"):
            return {}

        ssh_config = self._ssh_config

        # Lazy import - только когда реально нужен
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
        # Ваш существующий код получения данных с Pi-hole API
        data: Dict[str, Any] = {}

        # Получаем ARP-таблицу
        self._arp_cache = await self._get_arp_table()

        # Обогащаем данные устройств информацией из ARP
        for mac, info in data.items():
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

        return data