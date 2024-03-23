import os
import hikari
import lavalink
import lightbulb
import sentry_sdk
from lightbulb.ext import tasks
from sunbot.config import CONFIG
from sunbot.db.base import database
from sunbot.db.models.guild import Guild
from sunbot.lavalink.events import EventHandler


class Sunbot(lightbulb.BotApp):

    def __init__(self) -> None:
        super().__init__(
            token=CONFIG.discord_token,
            ignore_bots=True,
            prefix=None,
            intents=hikari.Intents.ALL,
            default_enabled_guilds=CONFIG.default_guilds
        )

        self.lavalink: lavalink.Client | None = None

    def run(self) -> None:
        self.event_manager.subscribe(hikari.StartingEvent, self.on_starting)
        self.event_manager.subscribe(hikari.StartedEvent, self.on_started)
        self.event_manager.subscribe(hikari.StoppingEvent, self.on_stopping)
        self.event_manager.subscribe(lightbulb.CommandErrorEvent, self.on_command_error)
        self.event_manager.subscribe(hikari.GuildAvailableEvent, self.on_guild_available)

        super().run(
            activity=hikari.Activity(
                name="Watching you",
                type=hikari.ActivityType.WATCHING)
        )

    async def on_starting(self, event: hikari.StartingEvent):
        await database.connect()

        # Configure sentry if available
        if CONFIG.sentry and CONFIG.sentry.dsn:
            sentry_sdk.init(
                dsn=CONFIG.sentry.dsn,
                traces_sample_rate=1.0
            )

    async def on_started(self, event: hikari.StartedEvent):
        # Configure Lavalink if available
        if CONFIG.lavalink and CONFIG.lavalink.host:
            self.lavalink = lavalink.Client(self.get_me().id)
            self.lavalink.add_node(
                host=CONFIG.lavalink.host,
                port=CONFIG.lavalink.port,
                password=CONFIG.lavalink.password,
                region='au',
                name='default-node'
            )
            self.lavalink.add_event_hooks(EventHandler())

        # Load Extensions
        for folder in os.listdir("sunbot/plugins"):
            self.load_extensions_from(os.path.join("sunbot/plugins/", folder))

        tasks.load(self)

    async def on_stopping(self, event: hikari.StoppingEvent):
        await database.disconnect()

    async def on_command_error(self, event: lightbulb.CommandErrorEvent):
        exc = event.exception

        if isinstance(exc, lightbulb.NotOwner):
            await event.context.respond(
                embed=hikari.Embed(
                        description="You need to be an owner to do that.",
                        color=hikari.Colour(0xd32f2f)
                    )
                )
            return
        elif isinstance(exc, lightbulb.MissingRequiredPermission):
            await event.context.respond(
                embed=hikari.Embed(
                        description="You do not have permission to use this command.",
                        color=hikari.Colour(0xd32f2f)
                    )
                )
            return
        elif isinstance(exc, lightbulb.CommandIsOnCooldown):
            await event.context.respond(
                embed=hikari.Embed(
                        description=f"You cannot use the command yet, please wait {exc.retry_after:.0f} seconds.",
                        color=hikari.Colour(0xd32f2f)
                    )
                )
            return

        elif isinstance(exc, lightbulb.errors.CheckFailure):
            # Assume that the check logs a good error
            return

        await event.context.respond(
            embed=hikari.Embed(
                    description="Something went wrong",
                    color=hikari.Colour(0xd32f2f)
                )
            )
        raise event.exception

    async def on_guild_available(self, event: hikari.GuildAvailableEvent):
        # Ensure that there is a Guild Node for every guild we join
        await Guild.objects.get_or_create(id=event.guild_id)
