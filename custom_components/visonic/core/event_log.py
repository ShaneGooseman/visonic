"""Event log file export helpers (XML via Jinja2 and CSV) with path validation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)


def resolve_allowed_log_path(config_dir: str, filename: str) -> str | None:
    """Resolve a log file path and ensure it stays within the Home Assistant config directory."""
    if not filename:
        return None
    base_dir = Path(config_dir).resolve()
    candidate = Path(filename)
    resolved = (candidate if candidate.is_absolute() else base_dir / candidate).resolve()
    try:
        resolved.relative_to(base_dir)
    except ValueError:
        _LOGGER.warning("Panel Event Log - Refusing to write outside config directory: %s", filename)
        return None
    return str(resolved)


def write_panel_event_log_files(
    available: int,
    total: int,
    templatedata: list[dict[str, Any]] | None,
    csvdata: str | None,
    xml_path: str | None,
    csv_path: str | None,
    config_path: str,
    template_filename: str,
    add_csv_title: bool,
) -> list[str]:
    """Write panel event log files in an executor thread. Returns error notifications to emit."""
    errors: list[str] = []
    try:
        if xml_path is not None:
            try:
                from jinja2 import Environment, FileSystemLoader

                file_loader = FileSystemLoader(
                    [
                        config_path + "/templates",
                        config_path + "/xml",
                        config_path + "/www",
                        config_path,
                    ],
                    followlinks=False,
                )
                env = Environment(loader=file_loader)
                template = env.get_template(template_filename)
                output = template.render(
                    entries=templatedata,
                    total=total,
                    available=f"{available}",
                )
                with open(xml_path, "w", encoding="utf-8") as f:
                    f.write(output.rstrip())
            except (IOError, AttributeError, TypeError):
                errors.append("Panel Event Log - Failed to write XML file")

        if csv_path is not None and csvdata is not None:
            try:
                content = csvdata
                if add_csv_title:
                    content = "current, total, partition, date, time, zone, event\n" + content
                with open(csv_path, "w", encoding="utf-8") as f:
                    f.write(content.rstrip())
            except (IOError, AttributeError, TypeError):
                errors.append("Panel Event Log - Failed to write CSV file")
    except Exception:
        errors.append("Panel Event Log - Failed to Create Valid Event Log Files")
    return errors
