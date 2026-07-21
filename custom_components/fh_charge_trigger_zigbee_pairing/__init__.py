"""Home Assistant integration for triggering Zigbee pairing on Futurehome Charge via BLE.

This module registers two services:
 - fh_charge_trigger_zigbee_pairing.scan (supports response)
 - fh_charge_trigger_zigbee_pairing.trigger

It now supports a simple GUI config flow that can store a default device MAC address.
"""

import logging
import asyncio
from bleak import BleakClient

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.components import bluetooth
from homeassistant.exceptions import HomeAssistantError

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from .const import (
    DOMAIN,
    DEFAULT_TARGET_NAME,
    CHAR2_UUID,
    CHAR3_UUID,
    CONF_DEVICE_MAC,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Charge Trigger Pairing component actions.

    This integration registers two services and optionally reads a configured
    default device MAC from the integration's config entry (if provided via the UI).
    """

    hass.data.setdefault(DOMAIN, {})

    def _get_default_mac() -> str | None:
        # Prefer user-provided config entry if present
        entries = hass.config_entries.async_entries(DOMAIN)
        if entries:
            return entries[0].data.get(CONF_DEVICE_MAC)
        return None

    async def handle_scan(call: ServiceCall) -> dict:
        """Scan for the charger and return its details as a response dictionary."""
        _LOGGER.info("Scanning active BLE advertisements for device: %s", DEFAULT_TARGET_NAME)

        # Get all live connectable advertisements caught by HA background scanners or proxies
        discovered_devices = bluetooth.async_discovered_service_info(hass, connectable=True)

        for service_info in discovered_devices:
            # Match against known name or raw broadcasted local_name
            if service_info.name == DEFAULT_TARGET_NAME or (
                service_info.advertisement and service_info.advertisement.local_name == DEFAULT_TARGET_NAME
            ):
                _LOGGER.info("Successfully discovered '%s' at %s", DEFAULT_TARGET_NAME, service_info.address)
                return {
                    "found": True,
                    "device_mac": service_info.address,
                    "rssi": service_info.rssi,
                }

        _LOGGER.warning("'%s' was not found in active Bluetooth advertisements.", DEFAULT_TARGET_NAME)
        return {"found": False, "device_mac": None, "rssi": None}

    async def handle_trigger_pairing(call: ServiceCall) -> None:
        """Connect to the verified explicit MAC address and trigger pairing."""
        device_mac = call.data.get("device_mac") or _get_default_mac()

        if not device_mac:
            raise HomeAssistantError("Missing required parameter: device_mac")

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
            client = await establish_connection(
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
                except Exception:  # best-effort disconnect
                    _LOGGER.debug("Error while disconnecting client", exc_info=True)

        except Exception as e:
            _LOGGER.error("Bluetooth tracking or transmission failure for %s: %s", device_mac, str(e))
            raise HomeAssistantError(f"Failed to communicate with BLE device {device_mac}: {e}")

    # Register actions
    hass.services.async_register(DOMAIN, "scan", handle_scan, supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "trigger", handle_trigger_pairing)

    return True
