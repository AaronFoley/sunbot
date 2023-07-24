from __future__ import annotations
from dataclasses import dataclass, field
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
class OpenAIAutoResponseConfig:
    """ Holds configuration for the openai module auto-response

        min_length (int): The minimum length for automatic responses
        prompt (str): The default prompt to include as context when generating a response
        cooldown (int): The time between auto responses in seconds
        trigger_chance (float): The chance that a particuluar message will trigger an auto response
        pre_context_time (int): Time in seconds to get messages before the selected one
        context_poll (int): The time to wait for more context messages to come in
        context_timeout (int): The maximum time we will wait before sending an auto reply
        completions_model (str): The completion model to use
        max_tokens (str): The max length of tokens to respond with
    """

    min_length: int = 10
    prompt: str = ("I want you to act as a user named Sunbot in a Discord server of close friends, "
                   "respond to the following with only your response, do not include the username:")
    cooldown: int = 600
    trigger_chance: float = 0.2
    pre_context_time: int = 120
    context_poll: int = 30
    context_timeout: int = 120
    completions_model: str = "text-davinci-003"
    max_tokens: int = 300


@dataclass
class OpenAIConfig:
    """ Holds configuration for the openai module 
        Attributes:
            api_key (str): The API key used for authenticating to the openai API
            command_cooldown (int): The time in seconds between using AI commands
            genimage_max_images (int): The maximum images you can ask chatGPT to generate
            ask_max_tokens (int): The max number of tokens open AI will respond to the ask command
            ask_completions_model (str): The Completion model to use for the ask command
    """

    api_key: str = None
    auto: OpenAIAutoResponseConfig = field(default_factory=OpenAIAutoResponseConfig)
    command_cooldown: int = 60
    genimage_max_images: int = 4
    ask_max_tokens: int = 500
    ask_completions_model: str = "text-davinci-003"
    response_context_time:int = 120
    response_max_tokens: int = 300
    response_completions_model: str = "text-davinci-003"
    response_prompt: str = ("I want you to act as a user named Sunbot in a Discord server of close friends, "
                            "respond to the following conversation that mentions you. Only include your response, do not include the username:")

@dataclass
class SentryConfig:
    dsn: str = None


@dataclass
class Config(JSONFileWizard):

    discord_token: str
    database: DatabaseConfig
    sentry: SentryConfig = None
    openai: OpenAIConfig = None
    lavalink: LavalinkConfig = None
    default_guilds: List[int] = ()


CONFIG = Config.from_json_file('config.json')
