from __future__ import annotations
from dataclasses import dataclass
from typing import List
from dataclass_wizard import JSONFileWizard


@dataclass
class LavalinkConfig:
    """ Holds the configuration for connecting to a LavaLink Instance 
        Attributes:
            host (str): The hostname to connect to
            password (str): Password to use when connecting
            port (int): The port to connect to, defaults to 2333
    """
    host: str
    password: str
    port: int = 2333


@dataclass
class DatabaseConfig:
    """ Holds configuration for connect to the Database
        Attributes:
            url (str): This is the full url to the database i.e. sqlite+aiosqlite:///example.db
    """
    url: str


@dataclass
class OpenAIConfig:
    """ Holds configuration for the openai module 
        Attributes:
            api_key (str): The API key used for authenticating to the openai API
            rate_limit (int): Rate limit in seconds applied to openai commands
            auto_min_length (int): The minimum length for automatic responses
            auto_prompt (str): The default prompt to include as context when generating a response
            auto_cooldown (int): The time between auto responses in seconds
            auto_trigger_chance (float): The chance that a particuluar message will trigger an auto response
            auto_pre_context_time (int): Time in seconds to get messages before the selected one
            auto_context_poll (int): The time to wait for more context messages to come in
            auto_context_timeout (int): The maximum time we will wait before sending an auto reply
            auto_completions_model (str): The completion model to use
            auto_max_tokens (str): The max length of tokens to respond with
    """

    api_key: str = None
    command_cooldown: int = 60
    auto_min_length: int = 10
    auto_prompt: str = "I want you to act as a user named Sunbot in a Discord server of close friends, respond to the following with only your response, do not include the username:"
    auto_cooldown: int = 600
    auto_trigger_chance: float = 0.2
    auto_pre_context_time: int = 120
    auto_context_poll: int = 30
    auto_context_timeout: int = 120
    auto_completions_model: str = "text-davinci-003"
    auto_max_tokens: int = 300


@dataclass
class Config(JSONFileWizard):

    discord_token: str
    database: DatabaseConfig

    openai: OpenAIConfig = None

    default_guilds: List[int] = ()
    lavalink: LavalinkConfig = None


CONFIG = Config.from_json_file('config.json')
