[![](https://img.shields.io/github/release/ShaneGooseman/visonic/all.svg?style=for-the-badge)](https://github.com/ShaneGooseman/visonic/releases)
[![](https://img.shields.io/badge/FORK%20MAINTAINER-%40ShaneGooseman-blue?style=for-the-badge)](https://github.com/ShaneGooseman)
[![](https://img.shields.io/badge/ORIGINAL%20AUTHOR-%40davesmeghead-green?style=for-the-badge)](https://github.com/davesmeghead/visonic)

[![Validated with HACS](https://github.com/ShaneGooseman/visonic/actions/workflows/validate.yaml/badge.svg)](https://github.com/ShaneGooseman/visonic/actions/workflows/validate.yaml)
[![Validate with hassfest](https://github.com/ShaneGooseman/visonic/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/ShaneGooseman/visonic/actions/workflows/hassfest.yaml)
[![Unit Tests](https://github.com/ShaneGooseman/visonic/actions/workflows/tests.yaml/badge.svg)](https://github.com/ShaneGooseman/visonic/actions/workflows/tests.yaml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

[English](#english) | [Español](#español)

---

<a name="english"></a>
# Visonic Alarm Panel for Home Assistant

This is a *custom integration* for [Home Assistant](https://www.home-assistant.io/), forked from [davesmeghead/visonic](https://github.com/davesmeghead/visonic) and modernized for Home Assistant Marketplace/HACS compliance, layered architecture (`core/` and `protocol/`), native diagnostic/measurement zone entities, hardened security, and improved `visonic_proxy` (PowerLink 3.1) interoperability.

## Introduction
This custom integration allows local control and monitoring of a Visonic alarm system over Ethernet (TCP / ESPHome / `visonic_proxy`) or USB/RS-232. Compatible models:

> **Note on `visonic_proxy`:** This integration is specifically designed to work with [`ShaneGooseman/visonic_proxy`](https://github.com/ShaneGooseman/visonic_proxy) (socket mode on port `5002` or WebSocket mode on port `8082`), although it also works with the original [`msp1974/visonic_proxy`](https://github.com/msp1974/visonic_proxy) from which it is forked.
- PowerMax+ (plus), PowerMax Express, PowerMax Pro, PowerMax Pro Plus, PowerMax Complete and PowerMax Complete Plus
- PowerMaster-10, PowerMaster-30 and PowerMaster-33
- PowerMaster-360 and PowerMaster-360R (limited to Standard Plus mode)

This Home Assistant Integration allows you to:
- Control the alarm panel to arm and disarm
- Bypass/Arm individual sensors
- Expose zones as native Home Assistant devices and entities, including diagnostic binary sensors (`Tamper`, `Battery`) and measurement sensors (`Temperature` °C, `Illuminance` lx) on supported PowerMaster detectors
- Use X10 and PGM switches (on supported panel types)
- On PowerMaster panels, trigger the Siren, Panic Alarm, Emergency and Fire alarms, and retrieve Camera PIR images
- Reconfigure Ethernet/USB connection parameters in-place without removing the integration
- Use Home Assistant UI in English, **Spanish**, French, Italian, and Dutch

## Documentation (Wiki)
Full documentation is maintained in this repository's Wiki (and mirrored under [`docs/wiki/`](docs/wiki/)):
- **English:** [Wiki Home](https://github.com/ShaneGooseman/visonic/wiki) (local copy: [`docs/wiki/Home.md`](docs/wiki/Home.md))
- **Español:** [Inicio de la Wiki (ES)](https://github.com/ShaneGooseman/visonic/wiki/Home-ES) (copia local: [`docs/wiki/Home-ES.md`](docs/wiki/Home-ES.md))

Release history is tracked in [`CHANGELOG.md`](CHANGELOG.md).

## Configuration
Set up this integration from the **Settings → Devices & Services** page within Home Assistant (manual Ethernet/USB setup, Zeroconf auto-discovery for compatible proxies, and in-place reconfiguration are supported).
To install via HACS, add `https://github.com/ShaneGooseman/visonic` as a custom repository (category: *Integration*) in HACS, install it, and restart Home Assistant.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=visonic)

---

<a name="español"></a>
# Panel de Alarma Visonic para Home Assistant

Esta es una *integración personalizada* para [Home Assistant](https://www.home-assistant.io/), bifurcada de [davesmeghead/visonic](https://github.com/davesmeghead/visonic) y modernizada con arquitectura por capas (`core/` y `protocol/`), compatibilidad con Home Assistant Marketplace/HACS, entidades nativas de diagnóstico y medición por zona, endurecimiento de seguridad e interoperabilidad mejorada con `visonic_proxy` (PowerLink 3.1).

## Introducción
Esta integración permite controlar y monitorizar de forma local un sistema de alarma Visonic mediante Ethernet (TCP / ESPHome / `visonic_proxy`) o USB/RS-232. Modelos compatibles:

> **Nota sobre `visonic_proxy`:** Esta integración está específicamente diseñada para trabajar con [`ShaneGooseman/visonic_proxy`](https://github.com/ShaneGooseman/visonic_proxy) (en modo socket `5002` o WebSocket `8082`), aunque también funciona con el [`msp1974/visonic_proxy`](https://github.com/msp1974/visonic_proxy) original del que es fork.
- PowerMax+ (plus), PowerMax Express, PowerMax Pro, PowerMax Pro Plus, PowerMax Complete y PowerMax Complete Plus
- PowerMaster-10, PowerMaster-30 y PowerMaster-33
- PowerMaster-360 y PowerMaster-360R (limitado a modo Standard Plus)

Con esta integración de Home Assistant puedes:
- Armar y desarmar el panel de alarma
- Anular (*bypass*) o reactivar sensores individuales
- Usar las zonas como dispositivos y entidades nativas de Home Assistant, incluyendo sensores binarios de diagnóstico (`Tamper`, `Batería`) y sensores de medición (`Temperatura` en °C, `Iluminancia` en lx) en detectores PowerMaster compatibles
- Controlar interruptores X10 y la salida PGM (en paneles compatibles)
- En paneles PowerMaster, disparar la sirena y alarmas de Pánico, Emergencia e Incendio, además de recuperar imágenes de cámaras PIR
- Reconfigurar la conexión Ethernet/USB directamente desde la interfaz sin eliminar la integración
- Utilizar la interfaz en **español**, inglés, francés, italiano y neerlandés

## Documentación (Wiki)
Toda la documentación actualizada está disponible en la Wiki de este repositorio (y reflejada en [`docs/wiki/`](docs/wiki/)):
- **Español:** [Inicio de la Wiki (ES)](https://github.com/ShaneGooseman/visonic/wiki/Home-ES) (copia local: [`docs/wiki/Home-ES.md`](docs/wiki/Home-ES.md))
- **English:** [Wiki Home](https://github.com/ShaneGooseman/visonic/wiki) (local copy: [`docs/wiki/Home.md`](docs/wiki/Home.md))

El historial de versiones se mantiene en [`CHANGELOG.md`](CHANGELOG.md).

## Configuración
Configura esta integración desde **Ajustes → Dispositivos y servicios** en Home Assistant (compatible con configuración manual Ethernet/USB, autodescubrimiento Zeroconf para proxies compatibles y reconfiguración sin borrar la integración).
Para instalarla con HACS, añade `https://github.com/ShaneGooseman/visonic` como repositorio personalizado (categoría *Integración*), instálala y reinicia Home Assistant.

[![Abre tu instancia de Home Assistant y comienza a configurar una nueva integración.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=visonic)
