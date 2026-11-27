> **Language / Idioma:** [Read in English](https://github.com/ShaneGooseman/visonic/wiki/Using-NodeMCU-PowermaxProModel6) | **Español**

# Uso de NodeMCU (`esp-link`) con PowerMax Pro

Esta guía explica cómo utilizar un **NodeMCU (ESP8266)** flasheado con **`esp-link`** como puente serie a TCP Wi-Fi entre una central Visonic PowerMax Pro y Home Assistant.

> **Aviso:** Modificar el hardware de la alarma es bajo tu propia responsabilidad y puede anular la garantía de Visonic.

## Hardware necesario
- NodeMCU v0.1 / v3 (ESP8266 CH340G)
- 4 cables puente
- Panel Visonic PowerMax Pro

## Patillaje y cableado (PowerMax Pro)

| Panel Visonic | Pin / Punto de soldadura | NodeMCU |
|---------------|--------------------------|---------|
| `3.75V` | `TP71` | `3.3V` |
| `GND` | `TP29` | `G` (GND) |
| `TX` | `TP35` | `RX` |
| `RX` | `TP33` | `TX` |

## Flasheo de `esp-link`
1. Descarga `esp-link` v3.0.14 desde [jeelabs/esp-link releases](https://github.com/jeelabs/esp-link/releases/tag/V3.0.14).
2. Instala `esptool`:
   ```bash
   pip install esptool
   ```
3. Comprueba el tamaño de la memoria flash y flashea los binarios extraídos (ajusta `/dev/ttyUSB0` y el tamaño de flash si es necesario):
   ```bash
   esptool.py --port /dev/ttyUSB0 flash_id
   esptool.py --port /dev/ttyUSB0 --baud 230400 write_flash -fs 4MB -ff 80m \
     0x00000 boot_v1.6.bin 0x1000 user1.bin \
     0x3FC000 esp_init_data_default.bin 0x3FE000 blank.bin
   ```

## Configuración de `esp-link`
1. Conéctate al punto de acceso Wi-Fi de `esp-link` y configúralo para conectarse a tu red doméstica (asigna una IP estática o reserva DHCP en tu router).
2. Desactiva los pines GPIO que no utilices en la página de asignación de pines.
3. Abre **µC Console** y ajusta la velocidad a `9600` baudios (o `38400` según el firmware del panel — ver [Configuración de hardware](https://github.com/ShaneGooseman/visonic/wiki/Hardware-Setup-ES#parámetros-rs-232-y-velocidad-en-baudios)).
4. Ten en cuenta que `esp-link` expone por defecto el puente serie transparente en el **puerto TCP `23`**.

## Configuración en Home Assistant
> **Nota actualizada:** La configuración mediante `configuration.yaml` **ya no está soportada**. Configura la integración desde la interfaz de Home Assistant:
1. Ve a **Ajustes → Dispositivos y servicios → + Añadir integración → Visonic Intruder Alarm**.
2. Selecciona **Ethernet**, introduce la IP fija de tu NodeMCU y el puerto **`23`**.

## Consejo: Probar el puerto serie desde Linux
```bash
sudo socat -d -d pty,link=/dev/ip1,raw,echo=0,waitslave tcp:192.168.1.123:23
screen /dev/ip1 9600
```
