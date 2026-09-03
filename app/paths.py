from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    resource_dir: Path
    config_file: Path
    database_file: Path
    lessons_file: Path
    knowledge_dir: Path


def get_app_paths() -> AppPaths:
    if getattr(sys, "frozen", False):
        resource_dir = Path(getattr(sys, "_MEIPASS"))
        executable_dir = Path(sys.executable).resolve().parent
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        )
        data_dir = local_app_data / "GuitarCoach"
        config_file = executable_dir / "config.local.json"
    else:
        resource_dir = Path(__file__).resolve().parents[1]
        data_dir = resource_dir / "data"
        config_file = resource_dir / "config.local.json"

    return AppPaths(
        resource_dir=resource_dir,
        config_file=config_file,
        database_file=data_dir / "guitar_agent.db",
        lessons_file=resource_dir / "lessons" / "lessons.json",
        knowledge_dir=resource_dir / "data" / "knowledge",
    )
