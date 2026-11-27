> **Language / Idioma:** **English** | [Leer en Español](https://github.com/ShaneGooseman/visonic/wiki/USR-WIFI232-D2-ES)

# Using a USR-WIFI232-D2 / USR-TCP232-T2 / E / E2

This guide covers configuring a **USR-TCP232-T2**, **USR-TCP232-E**, **USR-TCP232-E2** (wired Ethernet) or **USR-WIFI232-D2** (Wi-Fi) as a transparent TCP-to-TTL serial bridge between a Visonic PowerMax/PowerMaster panel and Home Assistant.

### Manufacturer Manuals
- [USR-TCP232-E](https://www.manualslib.com/manual/1221543/Usr-Usr-Tcp232-E.html)
- [USR-TCP232-E2](https://www.pusr.com/products/dual-ttl-to-ethernet-modules-usr-tcp232-e2.html)
- [USR-WIFI232-D2](https://www.pusr.com/download/WIFI/USR-WIFI232-D2-V1.0.12_en.pdf)
- [USR-TCP232-T2](https://www.pusr.com/download/M0/USR-TCP232-T2-User-Manual-V1.1.pdf)

## Default Credentials & Network Settings

### Wired Models (`USR-TCP232-T2`, `E`, `E2`)
- **IP Address:** `192.168.0.7`
- **Subnet Mask:** `255.255.255.0`
- **Username / Password:** `admin` / `admin`

Connect the module via Ethernet and browse to `http://192.168.0.7`. If your PC is on a different subnet, assign a temporary static IP such as `192.168.0.6`.

### Wi-Fi Model (`USR-WIFI232-D2`)
- **Default SSID:** `USR-WIFI232-D2_xxxx`
- **IP Address:** `10.10.100.254`
- **Subnet Mask:** `255.255.255.0`
- **Username / Password:** `admin` / `admin`

Connect to the module's Wi-Fi hotspot and browse to `http://10.10.100.254`.

## Configuration Steps
1. Configure the module as a **TCP Server** in **STA (Station)** mode with **Transparent Transmission Mode** enabled.
2. Disable any special framing, heartbeat packets, or RFC2217/special characters.
3. Set the TTL RS-232 serial parameters:
   - **Baud rate:** `9600` or `38400` depending on panel firmware (see [Hardware Setup](https://github.com/ShaneGooseman/visonic/wiki/Hardware-Setup#rs-232-settings--baud-rate))
   - **Data bits:** `8`, **Parity:** `None`, **Stop bits:** `1`
4. Assign a static IP address on your home LAN (or DHCP reservation) and choose a TCP port **> 1024**.
5. For `USR-WIFI232-D2`, configure your home Wi-Fi SSID and password.
6. Save and reboot the module, perform an optional [Loopback Test](https://github.com/ShaneGooseman/visonic/wiki#troubleshooting), then add the **Visonic Intruder Alarm** integration in Home Assistant using **Ethernet** with the module's IP and TCP port.

---

*Original integration and documentation by [@davesmeghead](https://github.com/davesmeghead/visonic). Maintained and updated in this fork by [@ShaneGooseman](https://github.com/ShaneGooseman/visonic).*
