# Changelog

Todos los cambios relevantes de este fork. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado [SemVer](https://semver.org/lang/es/).

All notable changes to this fork. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and [SemVer](https://semver.org/).

## [1.0.1] - 2026-11-28

### Español

#### Añadido

- Descripciones explicativas (`data_description` y `description`) en todos los pasos de configuración y opciones de la interfaz en español (`es.json`) e inglés (`en.json`).
- Pruebas unitarias en `tests/test_options_flow.py` para verificar el flujo de opciones con `entry.options` vacío y la cobertura de `data_description`.
- Documentación actualizada en `docs/wiki/Home-ES.md`, `docs/wiki/Home.md`, `docs/wiki/Version-History-ES.md` y `docs/wiki/Version-History.md`.

#### Corregido

- `VisonicOptionsFlowHandler.async_step_init` ahora combina `entry.data` y `entry.options` al validar el tipo de dispositivo y modo de emulación, permitiendo editar la configuración desde **Configurar** en cualquier momento (antes abortaba con `device_error` si `entry.options` estaba vacío), sin arrastrar parámetros de conexión a `entry.options` para no interferir con **Reconfigurar**.
- `update_listener` comprueba de forma segura `entry.runtime_data` mediante `getattr`.

### English

#### Added

- Explanatory field descriptions (`data_description` and `description`) across all UI config and options steps in English (`en.json`) and Spanish (`es.json`).
- Unit tests in `tests/test_options_flow.py` covering `OptionsFlow` with empty `entry.options` and `data_description` key coverage.
- Updated documentation in `docs/wiki/Home.md`, `docs/wiki/Home-ES.md`, `docs/wiki/Version-History.md`, and `docs/wiki/Version-History-ES.md`.

#### Fixed

- `VisonicOptionsFlowHandler.async_step_init` now merges `entry.data` and `entry.options` when checking device type and emulation mode, allowing users to edit options via **Configure** at any time (previously aborted with `device_error` when `entry.options` was empty), without copying connection fields into `entry.options` so **Reconfigure** continues to work cleanly.
- `update_listener` safely guards `entry.runtime_data` lookup with `getattr`.

## [1.0.0] - 2026-11-27

Primera release versionada del fork, partiendo de `0.12.6.0` de
[davesmeghead/visonic](https://github.com/davesmeghead/visonic). La numeración deja las cuatro partes heredadas del
linaje upstream (`0.12.6.0`) y pasa a SemVer de tres partes (`1.0.0`); `PLUGIN_VERSION` sigue reflejando la versión del
protocolo del panel, no la de la integración.

First versioned release of the fork, starting from `0.12.6.0` by
[davesmeghead/visonic](https://github.com/davesmeghead/visonic). The version leaves the four-part upstream lineage
(`0.12.6.0`) and moves to three-part SemVer (`1.0.0`); `PLUGIN_VERSION` keeps tracking the panel protocol version, not
the integration version.

### Español

#### Añadido

- Arquitectura por capas: módulos reorganizados en `core/` (cliente, transporte, coordinador de eventos, registro y
  esquema) y `protocol/` (protocolo, enums, EPROM y helpers).
- Entidades nativas de diagnóstico y medición por zona: `Tamper` y `Batería` como sensores binarios, y `Temperatura`
  (°C) e `Iluminancia` (lx) en detectores PowerMaster compatibles.
- Flujo de reconfiguración (`reconfigure`) para cambiar los parámetros de conexión Ethernet/USB sin borrar la
  integración.
- Traducciones de la interfaz al inglés, español, francés, italiano y neerlandés.
- Assets de marca (`brand/`) con icono y logo en variantes clara y oscura, categorías y acciones v7 para Home Assistant
  Marketplace/HACS.
- Wiki bilingüe (ES/EN) en `docs/wiki/`, con referencia explícita al autor original en todas las páginas.
- Tests unitarios (`tests/`, `unittest`) y workflows de CI para HACS, hassfest y pruebas.

#### Cambiado

- APIs modernas de Home Assistant: `Entity`/`Device` Registry, `has_entity_name`, ciclo de vida de `ConfigEntry` y
  tareas gestionadas.
- Reconexión con backoff exponencial y re-vinculación de entidades tras reconectar.
- Eliminada la E/S bloqueante: todo el camino de datos es asíncrono.

#### Corregido

- Fallos críticos de arranque y borrado de entidades no disponibles.
- Concurrencia de `asyncio`, callbacks, ciclo de tareas y uso de `SensorEntity`.
- Permisos por entidad renombrada (extracción de `registry_helper`).
- Se omite `Send.ALIVE` en modo bridge.
- Validación de longitudes de tramas y de EPROM.

#### Seguridad

- Endurecimiento del manejo de rutas del registro de eventos: se rechaza escribir fuera del directorio de
  configuración de Home Assistant.

### English

#### Added

- Layered architecture: modules split into `core/` (client, transport, event coordinator, registry and schema) and
  `protocol/` (protocol, enums, EPROM and helpers).
- Native per-zone diagnostic and measurement entities: `Tamper` and `Battery` binary sensors, plus `Temperature` (°C)
  and `Illuminance` (lx) on supported PowerMaster detectors.
- `reconfigure` flow to change Ethernet/USB connection parameters without removing the integration.
- UI translations for English, Spanish, French, Italian and Dutch.
- Brand assets (`brand/`) with light and dark icon/logo variants, categories and v7 actions for Home Assistant
  Marketplace/HACS.
- Bilingual wiki (EN/ES) under `docs/wiki/`, crediting the original author on every page.
- Unit tests (`tests/`, `unittest`) and CI workflows for HACS, hassfest and tests.

#### Changed

- Modern Home Assistant APIs: `Entity`/`Device` Registry, `has_entity_name`, `ConfigEntry` lifecycle and managed tasks.
- Reconnection with exponential backoff and entity re-linking after reconnect.
- Blocking I/O removed: the whole data path is asynchronous.

#### Fixed

- Critical startup failures and deletion of unavailable entities.
- `asyncio` concurrency, callbacks, task lifecycle and `SensorEntity` usage.
- Permissions for renamed entities (`registry_helper` extraction).
- `Send.ALIVE` is skipped in bridge mode.
- Frame and EPROM length validation.

#### Security

- Hardened event log path handling: writes outside the Home Assistant configuration directory are refused.

[1.0.0]: https://github.com/ShaneGooseman/visonic/releases/tag/v1.0.0
