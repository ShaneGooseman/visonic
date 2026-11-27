> **Language / Idioma:** **English** | [Leer en Español](https://github.com/ShaneGooseman/visonic/wiki/Using-NodeMCU-PowermaxProModel6-ES)

# Using NodeMCU (`esp-link`) with PowerMax Pro

This guide explains how to use a **NodeMCU (ESP8266)** flashed with **`esp-link`** as a Wi-Fi TCP-to-serial bridge between a Visonic PowerMax Pro and Home Assistant.

> **Disclaimer:** Modifying alarm hardware is at your own risk and may void your Visonic warranty.

## Hardware Required
- NodeMCU v0.1 / v3 (ESP8266 CH340G)
- 4 jumper wires
- Visonic PowerMax Pro panel

## Pinout & Wiring (PowerMax Pro)

| Visonic Panel | Pin / Test Point | NodeMCU |
|---------------|------------------|---------|
| `3.75V` | `TP71` | `3.3V` |
| `GND` | `TP29` | `G` (GND) |
| `TX` | `TP35` | `RX` |
| `RX` | `TP33` | `TX` |

## Flashing `esp-link`
1. Download `esp-link` v3.0.14 from [jeelabs/esp-link releases](https://github.com/jeelabs/esp-link/releases/tag/V3.0.14).
2. Install `esptool`:
   ```bash
   pip install esptool
   ```
3. Check flash size and flash the extracted firmware binaries (adjust `/dev/ttyUSB0` and flash size if needed):
   ```bash
   esptool.py --port /dev/ttyUSB0 flash_id
   esptool.py --port /dev/ttyUSB0 --baud 230400 write_flash -fs 4MB -ff 80m \
     0x00000 boot_v1.6.bin 0x1000 user1.bin \
     0x3FC000 esp_init_data_default.bin 0x3FE000 blank.bin
   ```

## Configuring `esp-link`
1. Connect to the `esp-link` Wi-Fi hotspot and join it to your home Wi-Fi network (configure a static IP or DHCP reservation on your router).
2. Disable unused GPIO pins in the pin assignment page.
3. Open **µC Console** and set the baud rate to `9600` (or `38400` depending on panel firmware — see [Hardware Setup](https://github.com/ShaneGooseman/visonic/wiki/Hardware-Setup#rs-232-settings--baud-rate)).
4. Note that `esp-link` exposes the transparent TCP-to-UART bridge on **port `23`** by default.

## Configuring Home Assistant
> **Updated note:** `configuration.yaml` setup is **no longer supported**. Configure the integration from the Home Assistant UI:
1. Go to **Settings → Devices & Services → + Add Integration → Visonic Intruder Alarm**.
2. Choose **Ethernet**, enter your NodeMCU's static IP address and port **`23`**.

## Tip: Testing Serial Output on Linux
```bash
sudo socat -d -d pty,link=/dev/ip1,raw,echo=0,waitslave tcp:192.168.1.123:23
screen /dev/ip1 9600
```
