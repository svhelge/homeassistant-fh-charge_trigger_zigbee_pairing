"""Config flow for FH Charge Trigger Zigbee Pairing integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_TARGET_NAME, CONF_DEVICE_MAC


class FHChargeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FH Charge pairing trigger."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(title=DEFAULT_TARGET_NAME, data=user_input)

        data_schema = vol.Schema({vol.Optional(CONF_DEVICE_MAC, default=""): str})
        return self.async_show_form(step_id="user", data_schema=data_schema)
