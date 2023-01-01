import os
import hikari
import lavaplayer
import asyncio
import lightbulb
from lightbulb.ext import tasks
from sunbot.config import CONFIG

bot = lightbulb.BotApp(
    CONFIG.discord_token,
    ignore_bots=True,
    prefix=None,
    intents=hikari.Intents.ALL
)

lavalink = lavaplayer.LavalinkClient(
    host=CONFIG.lavalink.host,
    port=2333,
    password=CONFIG.lavalink.password
)


@bot.listen(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent):
    lavalink.set_user_id(bot.get_me().id)
    lavalink.set_event_loop(asyncio.get_event_loop())
    lavalink.connect()


@bot.listen(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent):
    await lavalink.raw_voice_state_update(event.guild_id, event.state.user_id, event.state.session_id, event.state.channel_id)


@bot.listen(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent):
    await lavalink.raw_voice_server_update(event.guild_id, event.endpoint, event.token)


for folder in os.listdir("sunbot/plugins"):
    bot.load_extensions_from(os.path.join("sunbot/plugins/", folder))

tasks.load(bot)
