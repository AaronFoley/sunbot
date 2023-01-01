from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
from dataclass_wizard import JSONFileWizard


@dataclass
class LavalinkConfig:
    host: str
    password: str


@dataclass
class PunishmentConfig:
    channel: str
    songs: List[str]


@dataclass
class ClipConfig:
    path: str
    seek: int = 0


@dataclass
class Config(JSONFileWizard):

    discord_token: str
    lavalink: LavalinkConfig
    punishment: PunishmentConfig
    clips: Dict[str, ClipConfig]


CONFIG = Config.from_json_file('config.json')
