"""Config flow for FH Charge Trigger Zigbee Pairing integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_TARGET_NAME, CONF_DEVICE_MAC


class FHChargeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FH Charge pairing trigger."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        from .options_flow import OptionsFlowHandler

        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict | None = None):
        if user_input is not None:
            # Create entry without saving user input (keep config entries empty by default)
            return self.async_create_entry(title=DEFAULT_TARGET_NAME, data={})

        data_schema = vol.Schema({vol.Optional(CONF_DEVICE_MAC, default=""): str})
        return self.async_show_form(step_id="user", data_schema=data_schema)
