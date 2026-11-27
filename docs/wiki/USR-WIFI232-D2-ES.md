> **Language / Idioma:** [Read in English](https://github.com/ShaneGooseman/visonic/wiki/USR-WIFI232-D2) | **Español**

# Uso de USR-WIFI232-D2 / USR-TCP232-T2 / E / E2

Esta guía explica cómo configurar un módulo **USR-TCP232-T2**, **USR-TCP232-E**, **USR-TCP232-E2** (Ethernet cableado) o **USR-WIFI232-D2** (Wi-Fi) como puente serie TTL a TCP transparente entre un panel Visonic PowerMax/PowerMaster y Home Assistant.

### Manuales del fabricante
- [USR-TCP232-E](https://www.manualslib.com/manual/1221543/Usr-Usr-Tcp232-E.html)
- [USR-TCP232-E2](https://www.pusr.com/products/dual-ttl-to-ethernet-modules-usr-tcp232-e2.html)
- [USR-WIFI232-D2](https://www.pusr.com/download/WIFI/USR-WIFI232-D2-V1.0.12_en.pdf)
- [USR-TCP232-T2](https://www.pusr.com/download/M0/USR-TCP232-T2-User-Manual-V1.1.pdf)

## Valores predeterminados de red y acceso

### Modelos cableados (`USR-TCP232-T2`, `E`, `E2`)
- **Dirección IP:** `192.168.0.7`
- **Máscara de subred:** `255.255.255.0`
- **Usuario / Contraseña:** `admin` / `admin`

Conecta el módulo por Ethernet y abre `http://192.168.0.7` en tu navegador. Si tu PC está en otra subred, asigna temporalmente una IP estática como `192.168.0.6`.

### Modelo Wi-Fi (`USR-WIFI232-D2`)
- **SSID predeterminado:** `USR-WIFI232-D2_xxxx`
- **Dirección IP:** `10.10.100.254`
- **Máscara de subred:** `255.255.255.0`
- **Usuario / Contraseña:** `admin` / `admin`

Conéctate a la red Wi-Fi del módulo y abre `http://10.10.100.254`.

## Pasos de configuración
1. Configura el módulo como **TCP Server** en modo **STA (Station)** con **Transparent Transmission Mode** activado.
2. Desactiva cualquier opción especial de tramas, paquetes *heartbeat*, RFC2217 o inserción de caracteres especiales.
3. Ajusta el puerto serie RS-232 TTL:
   - **Baudios:** `9600` o `38400` según el firmware del panel (ver [Configuración de hardware](https://github.com/ShaneGooseman/visonic/wiki/Hardware-Setup-ES#parámetros-rs-232-y-velocidad-en-baudios))
   - **Bits de datos:** `8`, **Paridad:** `None`, **Bits de parada:** `1`
4. Asigna una dirección IP fija en tu red local (o reserva DHCP) y elige un puerto TCP **> 1024**.
5. En el `USR-WIFI232-D2`, configura el SSID y contraseña de tu red Wi-Fi doméstica.
6. Guarda y reinicia el módulo, realiza opcionalmente la [prueba de bucle (Loopback)](https://github.com/ShaneGooseman/visonic/wiki/Home-ES#solucion-de-problemas) y añade la integración **Visonic Intruder Alarm** en Home Assistant seleccionando **Ethernet** con la IP y el puerto TCP del módulo.

---

*Integración y documentación originales por [@davesmeghead](https://github.com/davesmeghead/visonic). Mantenida y actualizada en este fork por [@ShaneGooseman](https://github.com/ShaneGooseman/visonic).*
