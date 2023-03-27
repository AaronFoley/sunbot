import os
import hikari
import lavaplayer
import asyncio
import lightbulb
from lightbulb.ext import tasks
from sunbot.config import CONFIG
from sunbot.db.base import database
from sunbot.db.models.guild import Guild


bot = lightbulb.BotApp(
    CONFIG.discord_token,
    ignore_bots=True,
    prefix=None,
    intents=hikari.Intents.ALL,
    default_enabled_guilds=CONFIG.default_guilds
)


# TODO: Support lavalink not been available
lavalink = lavaplayer.LavalinkClient(
    host=CONFIG.lavalink.host,
    port=CONFIG.lavalink.port,
    password=CONFIG.lavalink.password
)


@bot.listen(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent):
    lavalink.set_user_id(bot.get_me().id)
    lavalink.set_event_loop(asyncio.get_event_loop())
    lavalink.connect()


@bot.listen(hikari.StartingEvent)
async def on_starting(event: hikari.StartingEvent):
    await database.connect()


@bot.listen(hikari.StoppingEvent)
async def on_stop(event: hikari.StoppingEvent):
    await database.disconnect()


@bot.listen(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent):
    await lavalink.raw_voice_state_update(event.guild_id, event.state.user_id, event.state.session_id, event.state.channel_id)


@bot.listen(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent):
    await lavalink.raw_voice_server_update(event.guild_id, event.endpoint, event.token)


@bot.listen(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    exc = event.exception

    if isinstance(exc, lightbulb.NotOwner):
        await event.context.respond(
           embed=hikari.Embed(
                description=f"You need to be an owner to do that.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    elif isinstance(exc, lightbulb.MissingRequiredPermission):
        await event.context.respond(
           embed=hikari.Embed(
                description=f"You do not have permission to use this command.",
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
    
    await event.context.respond(
           embed=hikari.Embed(
                description=f"Something went wrong",
                color=hikari.Colour(0xd32f2f)
            )
        )
    raise event.exception


@bot.listen(hikari.GuildAvailableEvent)
async def guild_available(event: hikari.GuildAvailableEvent):
    # Ensure that there is a Guild Node for every guild we join
    await Guild.objects.get_or_create(id=event.guild_id)


for folder in os.listdir("sunbot/plugins"):
    bot.load_extensions_from(os.path.join("sunbot/plugins/", folder))

tasks.load(bot)
