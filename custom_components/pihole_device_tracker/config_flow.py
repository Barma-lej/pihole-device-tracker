"""Config flow for Pi-hole Device Tracker."""

import voluptuous as vol
from typing import Any, Dict, Optional

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import PiholeAPIClient
from .const import CONF_INTERVAL, DEFAULT_INTERVAL, DOMAIN

CONF_HOST = "host"
CONF_API_KEY = "api_key"


async def validate_input(
    hass: HomeAssistant, data: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate the user input."""
    client = PiholeAPIClient(
        host=data[CONF_HOST],
        api_key=data.get(CONF_API_KEY),
    )

    if not await client.async_test_connection():
        raise ValueError("Cannot connect to Pi-hole")

    return {"title": f"Pi-hole ({data[CONF_HOST]})"}


class PiholeDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pi-hole Device Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )
            except ValueError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_API_KEY): str,
                vol.Optional(CONF_INTERVAL, default=DEFAULT_INTERVAL): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
