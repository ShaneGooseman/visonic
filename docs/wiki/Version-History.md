> **Language / Idioma:** **English** | [Leer en Español](https://github.com/ShaneGooseman/visonic/wiki/Version-History-ES)

# Version History & Releases

This fork is versioned independently from the upstream project. The version that Home Assistant and HACS display is the one declared in [`manifest.json`](https://github.com/ShaneGooseman/visonic/blob/master/custom_components/visonic/manifest.json) (`"version"`), and every release is published as a Git tag plus a [GitHub release](https://github.com/ShaneGooseman/visonic/releases).

- Canonical change history: [`CHANGELOG.md`](https://github.com/ShaneGooseman/visonic/blob/master/CHANGELOG.md)
- All releases: [Releases](https://github.com/ShaneGooseman/visonic/releases)

## `1.0.0` — 2026-11-27

First versioned release of the fork, based on `0.12.6.0` by [davesmeghead/visonic](https://github.com/davesmeghead/visonic). The version leaves the four-part numbering inherited from upstream (`0.12.6.0`) and moves to three-part SemVer (`1.0.0`); `PLUGIN_VERSION` keeps tracking the panel protocol version, not the integration version.

Release: [`v1.0.0`](https://github.com/ShaneGooseman/visonic/releases/tag/v1.0.0)

### Added
- **Layered architecture:** modules split into `core/` (client, transport, event coordinator, registry and schema) and `protocol/` (protocol, enums, EPROM and helpers).
- **Native per-zone entities:** `Tamper` and `Battery` binary sensors, plus `Temperature` (°C) and `Illuminance` (lx) on supported PowerMaster detectors.
- **In-place reconfiguration:** `reconfigure` flow to change Ethernet/USB parameters without removing the integration, plus Zeroconf auto-discovery.
- **Translations:** English, Spanish, French, Italian and Dutch.
- **Home Assistant Marketplace/HACS:** brand assets (`brand/`) with light and dark variants, categories and v7 actions.
- **Bilingual wiki (EN/ES)** under `docs/wiki/`, crediting the original author on every page.
- **Unit tests** (`tests/`) and CI workflows for HACS, hassfest and tests.

### Changed
- Modern Home Assistant APIs: `Entity`/`Device` Registry, `has_entity_name`, `ConfigEntry` lifecycle and managed tasks.
- Reconnection with exponential backoff and entity re-linking after reconnect.
- Blocking I/O removed: the whole data path is asynchronous.

### Fixed
- Critical startup failures and deletion of unavailable entities.
- `asyncio` concurrency, callbacks, task lifecycle and `SensorEntity` usage.
- Permissions for renamed entities.
- `Send.ALIVE` skipped in bridge mode; frame and EPROM length validation.

### Security
- Event log writes outside the Home Assistant configuration directory are refused; sensitive EPROM fields are redacted from attributes and diagnostics.

### Upgrading
Install `1.0.0` from HACS as usual. Entity names follow the `0.12.6.0` upstream breaking change, so installations already running this fork keep their entity IDs; the version bump itself introduces no data migration.

---

*Original integration and documentation by [@davesmeghead](https://github.com/davesmeghead/visonic). Maintained and updated in this fork by [@ShaneGooseman](https://github.com/ShaneGooseman/visonic).*
