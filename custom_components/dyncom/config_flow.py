"""Config flow for the Dyn.com Dynamic DNS integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DynComAuthError, DynComError, async_update_dns
from .const import (
    CONF_HOSTNAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MIN_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOSTNAME): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_REAUTH_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def _async_try_credentials(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Attempt a real update request and translate failures into form errors."""
    session = async_get_clientsession(hass)
    try:
        await async_update_dns(
            session, data[CONF_HOSTNAME], data[CONF_USERNAME], data[CONF_PASSWORD]
        )
    except DynComAuthError:
        return {"base": "invalid_auth"}
    except DynComError:
        return {"base": "cannot_connect"}
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected exception during Dyn.com setup")
        return {"base": "unknown"}
    return {}


class DynComConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Dyn.com Dynamic DNS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOSTNAME].lower())
            self._abort_if_unique_id_configured()

            errors = await _async_try_credentials(self.hass, user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_HOSTNAME], data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth when Dyn.com rejects the stored credentials."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for new credentials and verify them."""
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            data = {**reauth_entry.data, **user_input}
            errors = await _async_try_credentials(self.hass, data)
            if not errors:
                return self.async_update_reload_and_abort(reauth_entry, data=data)

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return DynComOptionsFlow(config_entry)


class DynComOptionsFlow(OptionsFlow):
    """Handle the update-interval option for Dyn.com Dynamic DNS."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the update interval option."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_interval = self._config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=current_interval
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_UPDATE_INTERVAL))
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
