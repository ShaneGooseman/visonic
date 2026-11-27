> **Language / Idioma:** **English** | [Leer en Español](https://github.com/ShaneGooseman/visonic/wiki/Panel-Stuff-ES)

# Visonic Alarm Panel Stuff

Technical notes collected from hardware testing on Visonic panels (tested on a PowerMaster 30 with the Dual RS-232 extension board disconnected).

## The Dual RS-232 Connector
Many Visonic panels have a 20-pin (2×10) IDC connector marked **Dual RS-232**.

Consensus pinout (with the notch on the left: odd pins on the left column top-to-bottom `1..19`, even pins on the right column `2..20`):
- **Pin 1 ↔ Pin 2:** Bridged together (signals module presence to the panel)
- **Pin 3 ↔ Pin 4:** Bridged together (signals module presence to the panel)
- **Pin 5:** Channel 1 Rx
- **Pin 6:** Channel 1 Tx
- **Pin 7:** Channel 2 Rx
- **Pin 8:** Channel 2 Tx
- **Pin 19:** Ground (GND)
- **Pin 20:** Vcc (3.3 V DC)

### Channel 1
Expects a modem (likely used by the GSM module), issuing `AT\r` and `+++` at 9600 baud.

### Channel 2
Channel 2 mirrors the PC/IP connector (`Tx` pin 8 has 0 Ω resistance to PC/IP `Tx` pin 5) and **cannot** be used simultaneously with the PC/IP connector:
- Connecting one adapter to PC/IP or Channel 2 individually works.
- Connecting two adapters simultaneously causes the panel to ignore traffic from Channel 2 while accepting only the PC/IP connector.

### Summary (Using with PowerLink 3.1)
- You **cannot** wire this integration directly in parallel on the Dual RS-232 header alongside a hardware PowerLink 3.1 module.
- However, you **can** use Home Assistant together with a PowerLink 3.1 module by placing [`visonic_proxy`](https://github.com/msp1974/visonic_proxy) in between and connecting this integration in **Powerlink (Bridged)** mode.
- The GSM module (Channel 1) can coexist with this integration.
