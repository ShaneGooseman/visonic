> **Language / Idioma:** [Read in English](https://github.com/ShaneGooseman/visonic/wiki/Panel-Stuff) | **Español**

# Notas técnicas del panel Visonic

Apuntes técnicos recopilados en pruebas de hardware sobre paneles Visonic (probado en un PowerMaster 30 con la placa de expansión Dual RS-232 desconectada).

## El conector Dual RS-232
Muchos paneles Visonic incluyen un conector IDC de 20 pines (2×10) etiquetado como **Dual RS-232**.

Patillaje de consenso (mirando el conector con la muesca a la izquierda: pines impares en la columna izquierda de arriba abajo `1..19`, pines pares en la columna derecha `2..20`):
- **Pin 1 ↔ Pin 2:** Puenteados entre sí (indican al panel que hay un módulo conectado)
- **Pin 3 ↔ Pin 4:** Puenteados entre sí (indican al panel que hay un módulo conectado)
- **Pin 5:** Canal 1 Rx
- **Pin 6:** Canal 1 Tx
- **Pin 7:** Canal 2 Rx
- **Pin 8:** Canal 2 Tx
- **Pin 19:** Masa (GND)
- **Pin 20:** Vcc (3.3 V CC)

### Canal 1
Espera un módem (utilizado normalmente por el módulo GSM), enviando comandos `AT\r` y `+++` a 9600 baudios.

### Canal 2
El Canal 2 replica el conector PC/IP (el pin 8 `Tx` está unido con 0 Ω al pin 5 `Tx` del conector PC/IP) y **no** puede utilizarse simultáneamente con el conector PC/IP:
- Conectar un único adaptador en PC/IP o en Canal 2 funciona correctamente.
- Conectar dos adaptadores al mismo tiempo hace que el panel ignore los datos del Canal 2 y solo atienda al conector PC/IP.

### Resumen (Uso junto a PowerLink 3.1)
- **No** es posible cablear esta integración en paralelo en el conector Dual RS-232 junto a un módulo hardware PowerLink 3.1.
- Sin embargo, **sí** puedes usar Home Assistant junto a un módulo PowerLink 3.1 utilizando [`visonic_proxy`](https://github.com/msp1974/visonic_proxy) y conectando esta integración en modo **Powerlink (Puenteado)**.
- El módulo GSM (Canal 1) sí puede coexistir con esta integración.
