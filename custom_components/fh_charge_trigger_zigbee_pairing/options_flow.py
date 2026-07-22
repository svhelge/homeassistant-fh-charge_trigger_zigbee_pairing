from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_MAC, DOMAIN

_MAC_RE = re.compile(r"^(?:[0-9A-F]{2}[:\-]){5}[0-9A-F]{2}$", re.I)


def _normalize_mac(mac: str) -> str:
    mac = (mac or "").strip().upper()
    mac = mac.replace("-", ":")
    if len(mac) == 12 and ":" not in mac:
        mac = ":".join(mac[i : i + 2] for i in range(0, 12, 2))
    return mac


def _is_valid_mac(mac: str) -> bool:
    mac = _normalize_mac(mac)
    return bool(_MAC_RE.match(mac))


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for the FH Charge Trigger Zigbee Pairing integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options for the config entry."""
        if user_input is not None:
            device_mac = user_input.get(CONF_DEVICE_MAC, "")
            device_mac = _normalize_mac(device_mac) if device_mac else ""

            if device_mac and not _is_valid_mac(device_mac):
                schema = vol.Schema({vol.Optional(CONF_DEVICE_MAC, default=self.config_entry.options.get(CONF_DEVICE_MAC, "")): str})
                return self.async_show_form(step_id="init", data_schema=schema, errors={"device_mac": "invalid_mac"})

            # Save options (empty string means unset)
            return self.async_create_entry(title="", data={CONF_DEVICE_MAC: device_mac})

        current = self.config_entry.options.get(CONF_DEVICE_MAC, "")
        schema = vol.Schema({vol.Optional(CONF_DEVICE_MAC, default=current): str})
        return self.async_show_form(step_id="init", data_schema=schema)
