# Futurehome Charge - Trigger Zigbee Pairing
**Futurehome Charge - Trigger Zigbee Pairing** is a lightweight Home Assistant custom integration designed to trigger Zigbee pairing mode on the Futurehome Charge EV charger over Bluetooth Low Energy (BLE).

By interfacing directly with Home Assistant’s native Bluetooth stack, this integration can automatically scan ambient BLE advertisements, confirm the presence of your Futurehome Charge, and dispatch the required GATT commands to open its Zigbee pairing window.

This module requires that the bluetooth integration is configured in Homeassistant.

The module adds two actions:

#### 1. `fh_charge_trigger_zigbee_pairing.scan`
Scans for visible Futurehome Charge BLE advertisements and returns response data for automations.
Returns: found (boolean), device_mac (string), rssi: (integer).

#### 2. `fh_charge_trigger_zigbee_pairing.trigger`
Connects to the specified MAC address and executes the GATT sequence to open Zigbee pairing.

Fields:
  * device_mac (Required): The target hardware MAC address (typically supplied by the scan action).
