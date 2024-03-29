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
class OpenAIAutoRandomConfig:
    """ Configuration for automatic random messages

        min_length (int): The minimum length for automatic responses
        cooldown (int): The time between auto responses in seconds
        trigger_chance (float): The chance that a particuluar message will trigger an auto response
        pre_context_time (int): Time in seconds to get messages before the selected one
        context_poll (int): The time to wait for more context messages to come in
        context_timeout (int): The maximum time we will wait before sending an auto reply
        max_tokens (str): The max length of tokens to respond with
    """

    min_length: int = 10
    cooldown: int = 600
    trigger_chance: float = 0.2
    pre_context_time: int = 120
    context_poll: int = 30
    context_timeout: int = 120
    max_tokens: int = 300


@dataclass
class OpenAIAutoReplyConfig:
    """ Config for Automatic Replies and Mentions

        pre_context_time (int): Time in seconds to get messages before the selected one
        pre_context_limit (int): The maximum amount of messages to send
        max_tokens (str): The max length of tokens to respond with
    """

    pre_context_limit: int = 100
    pre_context_time: int = 120
    max_tokens: int = 300


@dataclass
class OpenAIAutoConfig:
    """ Config for Sunbot's automatic responses to random messages, and mentions/replies

        system_context (list[str]): list of extra context to pass a system role to chat API
        completions_model (str): The completion model to use
        random (OpenAIAutoRandomConfig): Config for Random Responses
        reploy (OpenAIAutoReplyConfig): Config for Replies/Mentions
    """

    system_context: List[str] = (
        ("You are Sunbot, a member of a discord server. You will interact with users as if you are just "
         "another user in the channel. The format of messages from users will be <username>(<userId>): <message>."
         "Do not use this format in your replies"),

    )
    completions_model: str = "gpt-4-vision-preview"
    random: OpenAIAutoRandomConfig = field(default_factory=OpenAIAutoRandomConfig)
    reply: OpenAIAutoReplyConfig = field(default_factory=OpenAIAutoReplyConfig)

    @property
    def use_vision(self) -> bool:
        return 'vision' in self.completions_model.lower()


@dataclass
class OpenAIConfig:
    """ Holds configuration for the openai module
        Attributes:
            api_key (str): The API key used for authenticating to the openai API
            command_cooldown (int): The time in seconds between using AI commands
            genimage_max_images (int): The maximum images you can ask chatGPT to generate
            ask_max_tokens (int): The max number of tokens open AI will respond to the ask command
            ask_completions_model (str): The Completion model to use for the ask command
            auto (OpenAIAutoConfig): Config for auto responses
    """

    api_key: str = None
    command_cooldown: int = 60
    genimage_max_images: int = 4
    ask_max_tokens: int = 500
    ask_completions_model: str = "gpt-4-vision-preview"
    auto: OpenAIAutoConfig = field(default_factory=OpenAIAutoConfig)

    @property
    def ask_use_vision(self) -> bool:
        return 'vision' in self.completions_model.lower()


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
