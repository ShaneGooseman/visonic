> **Idioma / Language:** [Read in English](https://github.com/ShaneGooseman/visonic/wiki/Version-History) | **Español**

# Versiones e historial

Este fork se versiona de forma independiente del proyecto original. La versión que muestran Home Assistant y HACS es la declarada en [`manifest.json`](https://github.com/ShaneGooseman/visonic/blob/master/custom_components/visonic/manifest.json) (`"version"`), y cada release se publica como tag de Git más una [release de GitHub](https://github.com/ShaneGooseman/visonic/releases).

- Historial canónico de cambios: [`CHANGELOG.md`](https://github.com/ShaneGooseman/visonic/blob/master/CHANGELOG.md)
- Todas las releases: [Releases](https://github.com/ShaneGooseman/visonic/releases)

## `1.0.0` — 2026-11-27

Primera release versionada del fork, partiendo de `0.12.6.0` de [davesmeghead/visonic](https://github.com/davesmeghead/visonic). La numeración deja las cuatro partes heredadas del linaje upstream (`0.12.6.0`) y pasa a SemVer de tres partes (`1.0.0`); `PLUGIN_VERSION` sigue reflejando la versión del protocolo del panel, no la de la integración.

Release: [`v1.0.0`](https://github.com/ShaneGooseman/visonic/releases/tag/v1.0.0)

### Añadido
- **Arquitectura por capas:** módulos en `core/` (cliente, transporte, coordinador de eventos, registro y esquema) y `protocol/` (protocolo, enums, EPROM y helpers).
- **Entidades nativas por zona:** `Tamper` y `Batería` como sensores binarios, más `Temperatura` (°C) e `Iluminancia` (lx) en detectores PowerMaster compatibles.
- **Reconfiguración en caliente:** flujo `reconfigure` para cambiar parámetros Ethernet/USB sin borrar la integración, además de autodescubrimiento Zeroconf.
- **Traducciones:** inglés, español, francés, italiano y neerlandés.
- **Home Assistant Marketplace/HACS:** assets de marca (`brand/`) en variantes clara y oscura, categorías y acciones v7.
- **Wiki bilingüe (ES/EN)** en `docs/wiki/`, con el autor original referenciado en todas las páginas.
- **Tests unitarios** (`tests/`) y workflows de CI para HACS, hassfest y pruebas.

### Cambiado
- APIs modernas de Home Assistant: `Entity`/`Device` Registry, `has_entity_name`, ciclo de vida de `ConfigEntry` y tareas gestionadas.
- Reconexión con backoff exponencial y re-vinculación de entidades tras reconectar.
- Eliminada la E/S bloqueante: todo el camino de datos es asíncrono.

### Corregido
- Fallos críticos de arranque y borrado de entidades no disponibles.
- Concurrencia de `asyncio`, callbacks, ciclo de tareas y uso de `SensorEntity`.
- Permisos por entidad renombrada.
- `Send.ALIVE` omitido en modo bridge; validación de longitudes de tramas y EPROM.

### Seguridad
- Se rechaza escribir registros de eventos fuera del directorio de configuración de Home Assistant; los campos sensibles de la EPROM se redactan en atributos y diagnósticos.

### Actualización
Instala `1.0.0` desde HACS como de costumbre. Los nombres de entidad siguen el cambio incompatible de `0.12.6.0` del proyecto original, así que las instalaciones que ya usan este fork conservan sus `entity_id`; el salto de versión no introduce migración de datos.

---

*Integración y documentación originales por [@davesmeghead](https://github.com/davesmeghead/visonic). Mantenidas y actualizadas en este fork por [@ShaneGooseman](https://github.com/ShaneGooseman/visonic).*
