from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
import logging

from .const import (
    DOMAIN,
    CONF_AWAY_TIME,
    CONF_SCAN_INTERVAL,
    CONF_SSH_HOST,
    CONF_SSH_PORT,
    CONF_SSH_USERNAME,
    CONF_SSH_PASSWORD,
    DEFAULT_HOST,
    DEFAULT_PASSWORD,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_AWAY_TIME,
    DEFAULT_SSH_PORT,
    DEFAULT_SSH_USERNAME,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
    vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(int, vol.Range(min=5)),
    vol.Required(CONF_AWAY_TIME, default=DEFAULT_AWAY_TIME): vol.All(int, vol.Range(min=30)),
})

STEP_SSH_DATA_SCHEMA = vol.Schema({
    vol.Optional(CONF_SSH_HOST): str,
    vol.Optional(CONF_SSH_PORT, default=DEFAULT_SSH_PORT): int,
    vol.Optional(CONF_SSH_USERNAME, default=DEFAULT_SSH_USERNAME): str,
    vol.Optional(CONF_SSH_PASSWORD): str,
})


class PiholeDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Pi-hole Device Tracker config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="Pi-hole Device Tracker",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return PiholeOptionsFlowHandler(config_entry)


class PiholeOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler."""
    
    def __init__(self, config_entry):
        self._config_entry = config_entry
    
    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            _LOGGER.debug(f"Saving options: {user_input}")
            return self.async_create_entry(data=user_input)
        
        # Получаем текущие options или пустой словарь
        options = self._config_entry.options or {}
        data = self._config_entry.data
        
        _LOGGER.debug(f"Loading options: {options}")
        _LOGGER.debug(f"Loading data: {data}")
        
        schema = vol.Schema({
            # SSH настройки - из options (куда они сохраняются)
            vol.Optional(CONF_SSH_HOST, 
                default=options.get(CONF_SSH_HOST, "")): str,
            vol.Optional(CONF_SSH_PORT, 
                default=options.get(CONF_SSH_PORT, data.get(CONF_SSH_PORT, DEFAULT_SSH_PORT))): int,
            vol.Optional(CONF_SSH_USERNAME, 
                default=options.get(CONF_SSH_USERNAME, data.get(CONF_SSH_USERNAME, DEFAULT_SSH_USERNAME))): str,
            vol.Optional(CONF_SSH_PASSWORD, 
                default=options.get(CONF_SSH_PASSWORD, "")): str,
            # Основные настройки - из data или options
            vol.Required(CONF_SCAN_INTERVAL, 
                default=options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))): 
                vol.All(int, vol.Range(min=5)),
            vol.Required(CONF_AWAY_TIME, 
                default=options.get(CONF_AWAY_TIME, data.get(CONF_AWAY_TIME, DEFAULT_AWAY_TIME))): 
                vol.All(int, vol.Range(min=30)),
        })
        
        return self.async_show_form(step_id="init", data_schema=schema)