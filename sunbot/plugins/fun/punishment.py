import lightbulb
import hikari
import random
from sunbot.config import CONFIG
from sunbot.bot import lavalink


plugin = lightbulb.Plugin("Punishment")


@plugin.listener(hikari.GuildAvailableEvent)
async def guild_available_event(event: hikari.GuildAvailableEvent):

    if 'punishment_channels' not in plugin.bot.d:
        plugin.bot.d.punishment_channels = {}

    # Fetch and cache the punishment channel by name

    for channel in event.guild.get_channels().values():
        if channel.type != hikari.ChannelType.GUILD_VOICE:
            continue

        if channel.name == CONFIG.punishment.channel:
            plugin.bot.d.punishment_channels[event.guild_id] = channel.id


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_server_update(event: hikari.VoiceStateUpdateEvent):
    if event.state.user_id == plugin.bot.get_me().id:
        return

    punishment_ch = plugin.bot.d.punishment_channels.get(event.guild_id)

    # If this event is about joining the punishment channel
    if event.state.channel_id == punishment_ch:
        # If Sunbot is already busy ...
        if plugin.bot.cache.get_voice_state(event.guild_id, plugin.bot.get_me().id):
            return

        await plugin.bot.update_voice_state(event.guild_id, punishment_ch, self_deaf=True)
        await lavalink.wait_for_connection(event.guild_id)

        song = random.choice(CONFIG.punishment.songs)
        result = await lavalink.auto_search_tracks(song)
        await lavalink.play(event.guild_id, result[0])
        await lavalink.repeat(event.guild_id, True)

    # if this is a user leaving the punishment channel
    elif event.old_state is not None and event.old_state.channel_id == punishment_ch:
        bot_voice_status = plugin.bot.cache.get_voice_state(event.guild_id, plugin.bot.get_me().id)
        # If the bot is connected to the punishment channel
        if bot_voice_status and bot_voice_status.channel_id == punishment_ch:
            states = plugin.bot.cache.get_voice_states_view_for_channel(event.guild_id, punishment_ch)
            if len(states) == 1:
                await plugin.bot.update_voice_state(event.guild_id, None)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
