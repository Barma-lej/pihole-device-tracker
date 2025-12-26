"""Config flow for Pi-hole Device Tracker."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import PiholeAPIClient
from .const import (
    CONF_CONSIDER_AWAY,
    CONF_POLL_INTERVAL,
    DEFAULT_CONSIDER_AWAY,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class PiholeDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Pi-hole Device Tracker."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle initial step."""
        
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            # Check unique ID
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            
            try:
                # Test connection
                client = PiholeAPIClient(
                    host=user_input[CONF_HOST],
                    password=user_input.get(CONF_PASSWORD, ""),
                )
                
                is_connected = await client.test_connection()
                
                if not is_connected:
                    errors["base"] = "cannot_connect"
                else:
                    # Connection successful
                    return self.async_create_entry(
                        title=f"Pi-hole ({user_input[CONF_HOST]})",
                        data=user_input,
                    )
            
            except Exception as err:
                _LOGGER.error(f"Error in config flow: {err}")
                errors["base"] = "unknown"
        
        # Show form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PASSWORD, default=""): str,
                vol.Optional(
                    CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                ): int,
                vol.Optional(
                    CONF_CONSIDER_AWAY, default=DEFAULT_CONSIDER_AWAY
                ): int,
            }
        )
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
