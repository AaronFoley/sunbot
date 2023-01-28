from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
from dataclass_wizard import JSONFileWizard


@dataclass
class LavalinkConfig:
    host: str
    password: str
    port: int = 2333


@dataclass
class PunishmentConfig:
    channel: str
    songs: List[str]


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class Config(JSONFileWizard):

    discord_token: str
    database: DatabaseConfig

    punishment: PunishmentConfig

    lavalink: LavalinkConfig = None


CONFIG = Config.from_json_file('config.json')
