[![](https://img.shields.io/github/release/ShaneGooseman/visonic/all.svg?style=for-the-badge)](https://github.com/ShaneGooseman/visonic/releases)
[![](https://img.shields.io/badge/FORK%20MAINTAINER-%40ShaneGooseman-blue?style=for-the-badge)](https://github.com/ShaneGooseman)
[![](https://img.shields.io/badge/ORIGINAL%20AUTHOR-%40davesmeghead-green?style=for-the-badge)](https://github.com/davesmeghead/visonic)

[![Validated with HACS](https://github.com/ShaneGooseman/visonic/actions/workflows/validate.yaml/badge.svg)](https://github.com/ShaneGooseman/visonic/actions/workflows/validate.yaml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

# Visonic Alarm Panel for Home Assistant / Panel de Alarma Visonic

## English
Local Home Assistant custom integration for Visonic PowerMax and PowerMaster alarm panels over Ethernet (TCP / ESPHome / `visonic_proxy`) or USB/RS-232.

- Arm/disarm the alarm panel and bypass/arm individual sensors
- Native zone devices and entities, including diagnostic (`Tamper`, `Battery`) and measurement (`Temperature`, `Illuminance`) sensors
- X10/PGM switches and PowerMaster Siren/Panic/Fire/Emergency triggers and Camera PIR images
- Supports Zeroconf auto-discovery, in-place reconfiguration, and English/Spanish/French/Italian/Dutch translations
- Documentation: [Wiki Home (EN)](https://github.com/ShaneGooseman/visonic/wiki)

## Español
Integración personalizada local de Home Assistant para paneles de alarma Visonic PowerMax y PowerMaster por Ethernet (TCP / ESPHome / `visonic_proxy`) o USB/RS-232.

- Arma/desarma el panel y anula (*bypass*) o reactiva sensores individuales
- Dispositivos y entidades nativas por zona, incluyendo diagnóstico (`Tamper`, `Batería`) y medición (`Temperatura`, `Iluminancia`)
- Interruptores X10/PGM, disparo de sirena/pánico/incendio/emergencia e imágenes de cámaras PIR en PowerMaster
- Compatible con autodescubrimiento Zeroconf, reconfiguración directa e interfaz en español, inglés, francés, italiano y neerlandés
- Documentación: [Inicio de la Wiki (ES)](https://github.com/ShaneGooseman/visonic/wiki/Home-ES)

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=visonic)
