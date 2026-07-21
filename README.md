# Futurehome Charge - Trigger Zigbee Pairing
**Futurehome Charge - Trigger Zigbee Pairing**

is a lightweight Home Assistant custom integration designed to trigger Zigbee pairing mode on the Futurehome Charge EV charger over Bluetooth Low Energy (BLE).

By interfacing directly with Home Assistant’s native Bluetooth stack, this integration can automatically scan ambient BLE advertisements, confirm the presence of your Futurehome Charge, and dispatch a short GATT sequence to open the charger's Zigbee pairing window.

This module requires that the `bluetooth` integration is configured in Home Assistant.

The module adds two actions (Developer Tools → Actions):

#### 1. `fh_charge_trigger_zigbee_pairing.scan`
Scans for visible Futurehome Charge BLE advertisements and returns response data for automations.
Returns: `found` (boolean), `device_mac` (string), `rssi` (integer).

Optional: pass `{ "save": true }` to persist the discovered `device_mac` into this integration's config entry options so it can be used as a default for the trigger action.

#### 2. `fh_charge_trigger_zigbee_pairing.trigger`
Connects to the specified MAC address and executes the GATT sequence to open Zigbee pairing.

Fields:
  * `device_mac` (Optional if saved): The target hardware MAC address (typically supplied by the scan action). If omitted, the integration will use the saved `device_mac` in the integration options if present.


## Installation

There are two supported installation methods: via HACS (recommended) or manual installation.

### Install with HACS (recommended)
1. Open Home Assistant and go to HACS.
2. Select the **Integrations** tab.
3. Click the three-dot menu (top-right) and choose **Custom repositories**.
4. In the **Add custom repository** dialog, paste the repository URL:

   `https://github.com/svhelge/homeassistant-fh-charge_trigger_zigbee_pairing`

   - Select **Category:** `Integration`.
   - Click **Add**.
5. After adding, open HACS → Integrations, find **Futurehome Charge - Trigger Zigbee Pairing** and click **Install**.
6. Restart Home Assistant if prompted by HACS.
7. Add the integration in Home Assistant: Settings → Devices & Services → **Add Integration** → search for **Futurehome Charge - Trigger Zigbee Pairing** and follow the UI flow.

HACS will allow easier updates and visibility in the HACS UI when new releases are published.

### Manual installation
1. On your Home Assistant instance, open the configuration directory (where `configuration.yaml` lives). Create the custom_components folder if it does not exist:

   ```bash
   mkdir -p /config/custom_components
   ```

2. Clone or download the repository into the custom_components folder. Using git (recommended):

   ```bash
   cd /config/custom_components
   git clone https://github.com/svhelge/homeassistant-fh-charge_trigger_zigbee_pairing.git fh_charge_trigger_zigbee_pairing
   ```

   Or download the repository ZIP from GitHub and copy the `custom_components/fh_charge_trigger_zigbee_pairing` directory into your Home Assistant `custom_components` folder.

3. Restart Home Assistant.
4. Add the integration in Home Assistant: Settings → Devices & Services → **Add Integration** → search for **Futurehome Charge - Trigger Zigbee Pairing** and follow the UI flow.


## Usage

- Use Developer Tools → Actions to call the `fh_charge_trigger_zigbee_pairing.scan` action. If your charger advertises, the action returns `found`, `device_mac`, and `rssi`.
  - To save the discovered MAC as the integration default (so `trigger` may use it later without passing `device_mac`), call the scan action with `{ "save": true }` while the device is visible.

- Use Developer Tools → Actions to call the `fh_charge_trigger_zigbee_pairing.trigger` action and pass the `device_mac` to trigger Zigbee pairing, or omit `device_mac` to use the saved option.


## Notes
- This integration performs BLE writes to the device; ensure you trust the device and that only authorized users have access to actions.
- The integration normalizes and validates MAC addresses before saving or using them.
- If you want the integration to remember a device without using the scan+save flow, an Options flow may be added later to edit the saved MAC.


## Troubleshooting
- If `scan` does not find the device, verify the Home Assistant `bluetooth` integration is enabled and that the charger is advertising and in range.
- If `trigger` fails to connect, check the Home Assistant logs for detailed error information and ensure no other process is connected to the BLE device.
