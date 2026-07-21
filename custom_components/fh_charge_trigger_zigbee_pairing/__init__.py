"""Home Assistant integration for triggering Zigbee pairing on Futurehome Charge via BLE.

This module registers two services:
 - fh_charge_trigger_zigbee_pairing.scan (supports response)
 - fh_charge_trigger_zigbee_pairing.trigger

The scan service can optionally persist a discovered MAC into the integration's
config entry options (when called with {"save": true}). The trigger service will
use the device_mac passed in the call, or fall back to the saved option if present.
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, Optional

from bleak import BleakClient
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.components import bluetooth
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    DEFAULT_TARGET_NAME,
    CHAR2_UUID,
    CHAR3_UUID,
    CONF_DEVICE_MAC,
)

_LOGGER = logging.getLogger(__name__)

# Simple MAC normalization/validation
_MAC_RE = re.compile(r"^(?:[0-9A-F]{2}[:\-]){5}[0-9A-F]{2}$", re.I)


def _normalize_mac(mac: str) -> str:
    """Normalize a MAC to upper-case colon-separated format (AA:BB:CC:DD:EE:FF)."""
    if mac is None:
        return ""
    mac = mac.strip().upper()
    mac = mac.replace("-", ":")
    # If it's 12 hex chars without separators, insert colons
    if len(mac) == 12 and ":" not in mac:
        mac = ":".join(mac[i : i + 2] for i in range(0, 12, 2))
    return mac


def _is_valid_mac(mac: str) -> bool:
    """Return True if mac is in a valid MAC address format."""
    if not mac:
        return False
    mac = _normalize_mac(mac)
    return bool(_MAC_RE.match(mac))


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up component-level resources and register services.

    Services are registered once. Config entries intentionally store no data
    by default, but options can be updated when the user requests saving
    a discovered MAC.
    """
    data: Dict[str, Any] = hass.data.setdefault(DOMAIN, {})

    # Register services once
    if not data.get("services_registered"):

        async def handle_scan(call: ServiceCall) -> dict:
            """Scan for the charger and return details; optionally save found MAC."""
            _LOGGER.info("Scanning active BLE advertisements for device: %s", DEFAULT_TARGET_NAME)

            # Optional boolean flag to persist the found MAC into config entry options
            save_requested: bool = bool(call.data.get("save", False))

            # Get all live connectable advertisements caught by HA background scanners or proxies
            discovered_devices = bluetooth.async_discovered_service_info(hass, connectable=True)

            for service_info in discovered_devices:
                # Match against known name or raw broadcasted local_name
                if service_info.name == DEFAULT_TARGET_NAME or (
                    service_info.advertisement and service_info.advertisement.local_name == DEFAULT_TARGET_NAME
                ):
                    mac = _normalize_mac(service_info.address)
                    _LOGGER.info("Successfully discovered '%s' at %s (rssi=%s)", DEFAULT_TARGET_NAME, mac, service_info.rssi)

                    # If requested, persist the MAC into the first config entry's options
                    if save_requested:
                        entries = hass.config_entries.async_entries(DOMAIN)
                        if entries:
                            entry = entries[0]
                            if not _is_valid_mac(mac):
                                _LOGGER.warning("Discovered MAC '%s' does not appear valid; not saving", mac)
                            else:
                                new_options = dict(entry.options or {})
                                new_options[CONF_DEVICE_MAC] = mac
                                hass.config_entries.async_update_entry(entry, options=new_options)
                                _LOGGER.info("Saved device_mac %s into config entry %s options", mac, entry.entry_id)
                        else:
                            _LOGGER.warning("Save requested but no config entry exists; add the integration first to persist the MAC")

                    return {"found": True, "device_mac": mac, "rssi": service_info.rssi}

            _LOGGER.warning("'%s' was not found in active Bluetooth advertisements.", DEFAULT_TARGET_NAME)
            return {"found": False, "device_mac": None, "rssi": None}

        async def handle_trigger_pairing(call: ServiceCall) -> None:
            """Connect to the provided MAC (or saved option) and trigger pairing."""
            # device_mac priority: service call -> saved option in config entry
            device_mac: Optional[str] = call.data.get("device_mac")

            if not device_mac:
                # Try to read from config entry options
                entries = hass.config_entries.async_entries(DOMAIN)
                if entries:
                    device_mac = entries[0].options.get(CONF_DEVICE_MAC)
                    if device_mac:
                        _LOGGER.debug("Using saved device_mac from config entry %s", entries[0].entry_id)

            if not device_mac:
                raise HomeAssistantError("Missing required parameter: device_mac (provide in service data or save it via scan with save: true)")

            device_mac = _normalize_mac(device_mac)
            if not _is_valid_mac(device_mac):
                raise HomeAssistantError(f"Invalid device_mac format: {device_mac}")

            _LOGGER.info("Resolving Bluetooth client device routing for MAC: %s", device_mac)

            # Resolve backend instance tracking from proximity scanner pool
            ble_device = bluetooth.async_ble_device_from_address(hass, device_mac, connectable=True)

            if not ble_device:
                raise HomeAssistantError(
                    f"Device with MAC address {device_mac} is completely unreachable. Ensure it is in range and advertising."
                )

            try:
                # Establish robust connection
                _LOGGER.info("Establishing secure connection to %s...", device_mac)
                client: BleakClient = await establish_connection(
                    BleakClientWithServiceCache,
                    ble_device,
                    ble_device.name or ble_device.address,
                    max_attempts=3,  # Will retry up to 3 times before failing
                )

                try:
                    _LOGGER.info("Bluetooth link established with charger at %s", device_mac)

                    # Step 1: Arm payload sequence (Empty string byte buffer)
                    await client.write_gatt_char(CHAR3_UUID, b"", response=False)

                    # Settle window to prevent overlapping operations
                    await asyncio.sleep(0.5)

                    # Step 2: Trigger pairing action flag (0x04)
                    await client.write_gatt_char(CHAR2_UUID, bytes([0x04]), response=False)

                    _LOGGER.info("Zigbee pairing sequence successfully broadcast to charger.")

                finally:
                    # Ensure we ALWAYS clean up and disconnect the client, even if writes fail
                    try:
                        await client.disconnect()
                    except Exception:
                        _LOGGER.debug("Error while disconnecting client", exc_info=True)

            except Exception as e:
                _LOGGER.error("Bluetooth tracking or transmission failure for %s: %s", device_mac, str(e))
                raise HomeAssistantError(f"Failed to communicate with BLE device {device_mac}: {e}")

        # Register actions
        hass.services.async_register(DOMAIN, "scan", handle_scan, supports_response=SupportsResponse.ONLY)
        hass.services.async_register(DOMAIN, "trigger", handle_trigger_pairing)

        data["services_registered"] = True

    return True


async def async_setup_entry(hass: HomeAssistant, entry: Any) -> bool:
    """Set up a config entry.

    The config entry does not have to contain any data initially. Options may
    be added later by the scan service.
    """
    _LOGGER.debug("Config entry %s added for %s (no stored data)", entry.entry_id, entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Any) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Config entry %s removed", entry.entry_id)
    return True
