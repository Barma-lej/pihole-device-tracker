"""Config flow for Pi-hole Device Tracker integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import PiholeAPIClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
    }
)


class PiholeDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pi-hole Device Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()
            
            try:
                # Test connection to Pi-hole
                await self._async_test_connection(
                    user_input[CONF_HOST],
                    user_input[CONF_PASSWORD],
                )
            except ConnectionError:
                errors["base"] = "cannot_connect"
                _LOGGER.error(f"Cannot connect to Pi-hole at {user_input[CONF_HOST]}")
            except AuthenticationError:
                errors["base"] = "invalid_auth"
                _LOGGER.error(f"Authentication failed for Pi-hole at {user_input[CONF_HOST]}")
            except Exception as err:
                _LOGGER.error(f"Unexpected error: {err}")
                errors["base"] = "unknown"
            else:
                # Create entry if connection successful
                return self.async_create_entry(
                    title=f"Pi-hole ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_test_connection(
        self,
        host: str,
        password: str,
    ) -> bool:
        """Test connection to Pi-hole.
        
        Args:
            host: Pi-hole host IP or hostname
            password: Web interface password
            
        Returns:
            True if connection successful
            
        Raises:
            ConnectionError: If cannot connect to Pi-hole
            AuthenticationError: If authentication fails
        """
        try:
            client = PiholeAPIClient(
                host=host,
                password=password,
                timeout=10,
            )
            
            # Test connection
            is_connected = await client.async_test_connection()
            
            if not is_connected:
                raise AuthenticationError("Authentication failed with Pi-hole")
            
            return True
            
        except AuthenticationError:
            raise
        except Exception as err:
            _LOGGER.error(f"Connection test failed: {err}")
            if "authentication" in str(err).lower() or "401" in str(err):
                raise AuthenticationError(f"Invalid credentials: {err}")
            else:
                raise ConnectionError(f"Cannot connect to Pi-hole: {err}")


class ConnectionError(Exception):
    """Error connecting to Pi-hole."""


class AuthenticationError(Exception):
    """Error authenticating with Pi-hole."""
