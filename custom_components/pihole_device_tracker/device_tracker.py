from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import logging

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.const import STATE_HOME, STATE_NOT_HOME
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import (
    DOMAIN,
    ATTR_FIRST_SEEN,
    ATTR_LAST_QUERY,
    ATTR_NUM_QUERIES,
    ATTR_MAC_VENDOR,
    ATTR_IPS,
    ATTR_NAME,
    ATTR_DHCP_EXPIRES,
    ATTR_INTERFACE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    away_time = data["away_time"]

    trackers = [
        PiholeTracker(coordinator, mac, away_time)
        for mac in coordinator.data
    ]
    async_add_entities(trackers)

class PiholeTracker(CoordinatorEntity, TrackerEntity):
    """Presence via Pi-hole device tracker."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def _get_device_name(self) -> str:
        """Определить имя устройства: name → IP → MAC."""
        if self._mac not in self.coordinator.data:
            return self._mac
        
        info = self.coordinator.data[self._mac]
        
        # 1. Пробуем name
        name = info.get(ATTR_NAME)
        if name and name != "*" and name.strip():
            return name.strip()
        
        # 2. Пробуем IP
        ips = info.get(ATTR_IPS)
        if ips:
            # ips может быть списком или строкой
            if isinstance(ips, list) and ips:
                return ips[0]
            elif isinstance(ips, str) and ips:
                return ips
        
        # 3. Возвращаем MAC
        return self._mac

    def _sanitize_for_entity_id(self, name: str) -> str:
        """Преобразовать имя в допустимый entity_id."""
        # Удаляем спецсимволы, заменяем пробелы на _
        import re
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name)  # множественные _ → один _
        name = name.strip('_')
        return name.lower()[:64]  # ограничение длины

    def __init__(self, coordinator, mac: str, away_time: int) -> None:
        super().__init__(coordinator)
        self._mac = mac
        self._away = away_time
        
        # Формируем имя: name → IP → MAC
        device_name = self._get_device_name()
        
        # name для отображения
        self._attr_name = device_name
        
        # unique_id и entity_id на основе имени
        safe_name = self._sanitize_for_entity_id(device_name)
        self._attr_unique_id = f"{DOMAIN}_{safe_name}"
        
        _LOGGER.debug(f"Tracker created: MAC={mac}, name={device_name}, unique_id={self._attr_unique_id}")

    @property
    def is_connected(self) -> bool:
        if self._mac not in self.coordinator.data:
            return False

        last = self.coordinator.data[self._mac].get(ATTR_LAST_QUERY)
        if not isinstance(last, (int, float)):
            return False

        return (datetime.now(timezone.utc).timestamp() - last) <= self._away

    @property
    def state(self) -> str:
        """Override default to ensure we never see 'unknown'."""
        return STATE_HOME if self.is_connected else STATE_NOT_HOME

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._mac not in self.coordinator.data:
            return {}
        
        info = self.coordinator.data[self._mac]
        last = info.get(ATTR_LAST_QUERY)
        now_ts = datetime.now(timezone.utc).timestamp()
        
        return {
            "last_query": datetime.fromtimestamp(last, timezone.utc).isoformat()
            if isinstance(last, (int, float)) else None,
            "last_query_seconds_ago": int(now_ts - last)
            if isinstance(last, (int, float)) else None,
            "first_seen": datetime.fromtimestamp(info.get(ATTR_FIRST_SEEN), timezone.utc).isoformat()
            if isinstance(info.get(ATTR_FIRST_SEEN), (int, float)) else None,
            "num_queries": info.get(ATTR_NUM_QUERIES),
            "mac_vendor": info.get(ATTR_MAC_VENDOR),
            "ips": info.get(ATTR_IPS),
            "name": info.get(ATTR_NAME),
            "dhcp_expires": datetime.fromtimestamp(info.get(ATTR_DHCP_EXPIRES), timezone.utc).isoformat()
            if isinstance(info.get(ATTR_DHCP_EXPIRES), (int, float)) else None,
            "interface": info.get(ATTR_INTERFACE),
        }

    @property
    def device_info(self) -> DeviceInfo:
        info = self.coordinator.data[self._mac]
        name = info.get(ATTR_NAME)
        if not name or name == "*" or not name.strip():
            name = self._mac
        return DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, self._mac)},
            name=name,
            manufacturer=info.get(ATTR_MAC_VENDOR),
            model=None,
        )