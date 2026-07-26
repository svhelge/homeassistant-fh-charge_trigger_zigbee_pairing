# Futurehome Charge – Trigger Zigbee Pairing

A custom Home Assistant integration that triggers Zigbee pairing mode on the **Futurehome Charge EV charger** over Bluetooth Low Energy (BLE). 
By leveraging Home Assistant’s native Bluetooth stack, it scans for nearby chargers and dispatches the GATT sequence required to open the charger's Zigbee pairing window.

💡 **Note:** This integration is typically **only used once** during initial setup. Once your charger is paired to your Zigbee network, you can safely disable or delete the integration.

 **Prerequisite:** Home Assistant’s native **Bluetooth integration** must be configured and active.

---

## Available Actions

Access these via **Developer Tools → Actions**:

### 1. `fh_charge_trigger_zigbee_pairing.scan`
Scans for visible Futurehome Charge BLE advertisements.
* **Returns:** `found` (boolean), `device_mac` (string), `rssi` (integer).
* **Optional Data:** Pass `{"save": true}` to automatically persist the discovered MAC address into the integration options for future use.

### 2. `fh_charge_trigger_zigbee_pairing.trigger`
Connects to the charger via BLE and executes the GATT sequence to enable Zigbee pairing.
* **Fields:** 
  * `device_mac` *(Optional if saved)*: The target hardware MAC address. If omitted, the saved MAC address is used.

---

## Installation

### Method 1: HACS (Recommended)
1. Open **HACS** → **Integrations** tab.
2. Click the top-right **three-dot menu** → **Custom repositories**.
3. Add repository URL: `https://github.com/svhelge/homeassistant-fh-charge_trigger_zigbee_pairing`
4. Set Category to **Integration** and click **Add**.
5. Find **Futurehome Charge - Trigger Zigbee Pairing**, click **Install**, and restart Home Assistant when prompted.
6. Navigate to **Settings → Devices & Services → Add Integration** and search for **Futurehome Charge - Trigger Zigbee Pairing**.

### Method 2: Manual Installation
1. Clone or copy the `fh_charge_trigger_zigbee_pairing` folder into your custom components directory:
   ```bash
   cd /config/custom_components
   git clone https://github.com/svhelge/homeassistant-fh-charge_trigger_zigbee_pairing.git fh_charge_trigger_zigbee_pairing
   ```
2. Restart Home Assistant.
3. Add via **Settings → Devices & Services → Add Integration**.

---

## Usage Workflow

1. **Scan:** Call `fh_charge_trigger_zigbee_pairing.scan` (with `save: true` to cache the MAC address).
2. **Trigger:** Call `fh_charge_trigger_zigbee_pairing.trigger` to open the charger's pairing window.
3. **Pair:** Start scanning on your Zigbee coordinator (ZHA, Zigbee2MQTT, etc.) to join the charger to your network.
4. **Cleanup (Optional):** Disable or delete this integration once pairing is complete.

---

## Troubleshooting

* **Scan Fails:** Verify the HA Bluetooth integration is functional, and the charger is powered on, advertising, and within range.
* **Trigger Fails:** Ensure no other BLE devices are connected to the charger and check the Home Assistant logs for detailed connection errors.



