from __future__ import annotations
from dataclasses import dataclass
from typing import List
from dataclass_wizard import JSONFileWizard


@dataclass
class LavalinkConfig:
    host: str
    password: str
    port: int = 2333


@dataclass
class DatabaseConfig:
    url: str


@dataclass
class Config(JSONFileWizard):

    discord_token: str
    database: DatabaseConfig

    default_guilds: List[int] = ()
    lavalink: LavalinkConfig = None


CONFIG = Config.from_json_file('config.json')
