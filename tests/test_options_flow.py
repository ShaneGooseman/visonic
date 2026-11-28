"""Unit tests for VisonicOptionsFlowHandler and translation data_description."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

VISONIC_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "visonic"


def _build_ha_stubs() -> dict[str, ModuleType]:
    """Create minimal Home Assistant and voluptuous stubs for config_flow import."""
    vol = ModuleType("voluptuous")

    class _Schema:
        def __init__(self, schema: object) -> None:
            self.schema = schema

    class _Marker:
        def __init__(self, key: str, default: object = None) -> None:
            self.schema = key
            self._default = default

        def default(self) -> object:
            return self._default

        def __str__(self) -> str:
            return self.schema

        def __hash__(self) -> int:
            return hash(self.schema)

        def __eq__(self, other: object) -> bool:
            return str(self) == str(other)

    vol.Schema = _Schema
    vol.Required = lambda key, default=None: _Marker(key, default)
    vol.Optional = lambda key, default=None: _Marker(key, default)
    vol.In = lambda values: values
    vol.Invalid = ValueError
    vol_sb = ModuleType("voluptuous.schema_builder")
    vol_sb.UNDEFINED = object()

    ha = ModuleType("homeassistant")
    ha_const = ModuleType("homeassistant.const")
    ha_const.CONF_DEVICE = "device"
    ha_const.CONF_HOST = "host"
    ha_const.CONF_PATH = "path"
    ha_const.CONF_PORT = "port"
    ha_const.CONF_USERNAME = "username"
    ha_const.CONF_PASSWORD = "password"
    ha_const.CONF_LANGUAGE = "language"
    ha_const.CONF_NAME = "name"
    ha_const.CONF_SOURCE = "source"
    ha_const.UnitOfTime = SimpleNamespace(SECONDS="s")
    ha_const.Platform = SimpleNamespace(
        ALARM_CONTROL_PANEL="alarm_control_panel",
        BINARY_SENSOR="binary_sensor",
        IMAGE="image",
        SELECT="select",
        SENSOR="sensor",
        SIREN="siren",
        SWITCH="switch",
    )

    ha_core = ModuleType("homeassistant.core")
    ha_core.callback = lambda fn: fn

    ha_helpers = ModuleType("homeassistant.helpers")
    ha_cv = ModuleType("homeassistant.helpers.config_validation")
    ha_cv.positive_int = int
    ha_cv.entity_id = str
    ha_selector = ModuleType("homeassistant.helpers.selector")
    for cls_name in (
        "ObjectSelector",
        "SelectOptionDict",
        "SelectSelector",
        "SelectSelectorConfig",
        "SelectSelectorMode",
        "SerialPortSelector",
        "EntitySelector",
        "EntitySelectorConfig",
        "TextSelector",
        "TextSelectorConfig",
        "NumberSelector",
        "NumberSelectorConfig",
    ):
        setattr(ha_selector, cls_name, type(cls_name, (), {"__init__": lambda self, *a, **kw: None}))
    ha_selector.TextSelectorType = SimpleNamespace(PASSWORD="password")
    ha_selector.NumberSelectorMode = SimpleNamespace(BOX="box")
    ha_selector.validate_selector = lambda x: x
    ha_helpers.config_validation = ha_cv
    ha_helpers.selector = ha_selector

    ha_util_yaml_obj = ModuleType("homeassistant.util.yaml.objects")
    ha_util_yaml_obj.NodeListClass = list
    ha_util_yaml = ModuleType("homeassistant.util.yaml")
    ha_util = ModuleType("homeassistant.util")
    ha_zc = ModuleType("homeassistant.helpers.service_info.zeroconf")
    ha_zc.ZeroconfServiceInfo = object
    ha_si = ModuleType("homeassistant.helpers.service_info")

    class _FlowHandler:
        def async_show_form(self, **kwargs: object) -> dict[str, object]:
            return {"type": "form", **kwargs}

        def async_abort(self, **kwargs: object) -> dict[str, object]:
            return {"type": "abort", **kwargs}

        def async_create_entry(self, **kwargs: object) -> dict[str, object]:
            return {"type": "create_entry", **kwargs}

    ha_def = ModuleType("homeassistant.data_entry_flow")
    ha_def.FlowHandler = _FlowHandler

    class _ConfigFlow(_FlowHandler):
        def __init_subclass__(cls, **kwargs: object) -> None:
            pass

    class _OptionsFlow(_FlowHandler):
        config_entry = None

    ha_ce = ModuleType("homeassistant.config_entries")
    ha_ce.ConfigEntry = object
    ha_ce.ConfigFlow = _ConfigFlow
    ha_ce.ConfigFlowResult = dict
    ha_ce.OptionsFlow = _OptionsFlow

    cc_pkg = ModuleType("custom_components")
    cc_pkg.__path__ = [str(VISONIC_DIR.parent)]
    vis_pkg = ModuleType("custom_components.visonic")
    vis_pkg.__path__ = [str(VISONIC_DIR)]

    ha_comp = ModuleType("homeassistant.components")
    ha_acp = ModuleType("homeassistant.components.alarm_control_panel")
    ha_acp.AlarmControlPanelState = SimpleNamespace(
        DISARMED="disarmed",
        ARMED_HOME="armed_home",
        ARMED_AWAY="armed_away",
        ARMED_NIGHT="armed_night",
        ARMING="arming",
        PENDING="pending",
        TRIGGERED="triggered",
    )

    class _GenericKey:
        def __init__(self, key: str) -> None:
            self.key = key

        def __class_getitem__(cls, _item: object) -> type[_GenericKey]:
            return cls

    ha_util_hass_dict = ModuleType("homeassistant.util.hass_dict")
    ha_util_hass_dict.HassKey = _GenericKey
    ha_util_hass_dict.HassEntryKey = _GenericKey

    return {
        "custom_components": cc_pkg,
        "custom_components.visonic": vis_pkg,
        "voluptuous": vol,
        "voluptuous.schema_builder": vol_sb,
        "homeassistant": ha,
        "homeassistant.components": ha_comp,
        "homeassistant.components.alarm_control_panel": ha_acp,
        "homeassistant.util.hass_dict": ha_util_hass_dict,
        "homeassistant.const": ha_const,
        "homeassistant.core": ha_core,
        "homeassistant.helpers": ha_helpers,
        "homeassistant.helpers.config_validation": ha_cv,
        "homeassistant.helpers.selector": ha_selector,
        "homeassistant.helpers.service_info": ha_si,
        "homeassistant.helpers.service_info.zeroconf": ha_zc,
        "homeassistant.util": ha_util,
        "homeassistant.util.yaml": ha_util_yaml,
        "homeassistant.util.yaml.objects": ha_util_yaml_obj,
        "homeassistant.data_entry_flow": ha_def,
        "homeassistant.config_entries": ha_ce,
    }


def _run_coro(coro: object) -> object:
    """Drive an async coroutine without creating a socket-based event loop."""
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    raise AssertionError("Coroutine yielded unexpectedly")


class TestOptionsFlowAndTranslations(unittest.TestCase):
    """Tests for OptionsFlow editing and translation data_description."""

    def test_options_flow_init_works_with_empty_options(self) -> None:
        """OptionsFlow must open parameters10 even when entry.options is empty."""
        stubs = _build_ha_stubs()
        custom_components_root = str(VISONIC_DIR.parent.parent)
        added_path = False
        if custom_components_root not in sys.path:
            sys.path.insert(0, custom_components_root)
            added_path = True

        try:
            with patch.dict(sys.modules, stubs):
                cf = importlib.import_module("custom_components.visonic.config_flow")

                entry = SimpleNamespace(
                    data={
                        "type": "ethernet",
                        "host": "192.168.1.50",
                        "port": "8080",
                        "panel_number": 0,
                        "emulation_mode": "Powerlink Emulation",
                    },
                    options={},
                )
                handler = cf.VisonicOptionsFlowHandler()
                handler.config_entry = entry

                result = _run_coro(handler.async_step_init())
                self.assertEqual(result["type"], "form")
                self.assertEqual(result["step_id"], "parameters10")
                self.assertNotIn("host", handler.config)

                res11 = _run_coro(handler.async_step_parameters10({"retry_connection_count": 2}))
                self.assertEqual(res11["step_id"], "parameters11")
                res12 = _run_coro(handler.async_step_parameters11({"motion_off_delay": 60}))
                self.assertEqual(res12["step_id"], "parameters12")
                res13 = _run_coro(handler.async_step_parameters12({"arm_away_instant": False}))
                self.assertEqual(res13["step_id"], "parameters13")
                done = _run_coro(handler.async_step_parameters13({"panellog_max_entries": 500}))
                self.assertEqual(done["type"], "create_entry")
                self.assertEqual(done["data"]["arm_away_instant"], False)
                self.assertNotIn("host", done["data"])
        finally:
            for mod_name in list(sys.modules):
                if mod_name.startswith("custom_components.visonic"):
                    del sys.modules[mod_name]
            if added_path:
                sys.path.remove(custom_components_root)

    def test_en_and_es_translations_have_data_description_for_all_fields(self) -> None:
        """Every config/options step with data must define data_description for all keys."""
        for lang in ("en", "es"):
            payload = json.loads((VISONIC_DIR / "translations" / f"{lang}.json").read_text(encoding="utf-8"))
            for section in ("config", "options"):
                for step_id, step_obj in payload[section]["step"].items():
                    if "data" not in step_obj:
                        continue
                    self.assertIn(
                        "data_description",
                        step_obj,
                        f"Missing data_description in {lang}.json {section}.step.{step_id}",
                    )
                    self.assertEqual(
                        set(step_obj["data"].keys()),
                        set(step_obj["data_description"].keys()),
                        f"Mismatch data vs data_description in {lang}.json {section}.step.{step_id}",
                    )


if __name__ == "__main__":
    unittest.main()
