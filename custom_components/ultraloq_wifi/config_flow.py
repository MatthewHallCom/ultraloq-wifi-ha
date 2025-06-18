"""Config flow for Ultraloq Wifi integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import UltraloqApiClient, UltraloqApiError, UltraloqAuthError
from .const import CONF_ADDRESS_ID, CONF_EMAIL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ultraloq Wifi."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_client: UltraloqApiClient | None = None
        self._user_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            # Validate credentials by attempting to authenticate
            session = async_get_clientsession(self.hass)
            api_client = UltraloqApiClient(session)

            try:
                if await api_client.authenticate(email, password):
                    await self.async_set_unique_id(email)
                    self._abort_if_unique_id_configured()

                    # Store API client and user data for address selection step
                    self._api_client = api_client
                    self._user_data = user_input

                    # Get addresses and proceed to address selection step
                    return await self.async_step_address()
                else:
                    errors["base"] = "auth_failed"
            except UltraloqAuthError:
                errors["base"] = "invalid_auth"
            except UltraloqApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during authentication")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_address(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the address selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Complete the setup with selected address
            address_id = user_input[CONF_ADDRESS_ID]
            final_data = {**self._user_data, CONF_ADDRESS_ID: address_id}

            return self.async_create_entry(
                title=f"Ultraloq Wifi ({self._user_data[CONF_EMAIL]})",
                data=final_data,
            )

        # Get addresses from API
        if not self._api_client:
            return self.async_abort(reason="no_api_client")

        try:
            addresses = await self._api_client.get_addresses()
            if not addresses:
                return self.async_abort(reason="no_addresses")

            # Create options for address selection
            address_options = {str(addr["id"]): addr["name"] for addr in addresses}

            address_schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS_ID): vol.In(address_options),
                }
            )

            return self.async_show_form(
                step_id="address",
                data_schema=address_schema,
                errors=errors,
            )

        except UltraloqApiError as err:
            _LOGGER.error("Failed to get addresses: %s", err)
            return self.async_abort(reason="cannot_get_addresses")