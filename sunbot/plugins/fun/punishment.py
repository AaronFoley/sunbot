from typing import Dict, Optional
import time
import logging
import random
import hikari
import lightbulb
import lavalink
from sunbot.db.models.punishment import PunishmentConfig, PunishmentSong
from sunbot.lavalink.voice import LavalinkVoice

logger = logging.getLogger(__name__)
plugin = lightbulb.Plugin("Punishment")


MAX_PUNISHMENT_TIME = 60


@plugin.command
@lightbulb.command("punish", "Commands related to the punishment channel")
@lightbulb.implements(lightbulb.commands.SlashCommandGroup)
async def punish_group(ctx: lightbulb.context.SlashContext):
    pass


@punish_group.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("channel", "Name of the channel", type=hikari.GuildVoiceChannel, channel_types=[hikari.ChannelType.GUILD_VOICE])
@lightbulb.command("channel", "Sets the punishment channel", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def set_channel(ctx: lightbulb.context.SlashContext, channel: hikari.InteractionChannel):
    config, _ = await PunishmentConfig.objects.get_or_create(guild=ctx.guild_id)

    config.channel = channel.id
    await config.upsert()

    await ctx.respond(
        hikari.Embed(
            description=f"Punishment Channel set to <#{channel.id}>",
            color=hikari.Colour(0x2ECC71)
        )
    )


@punish_group.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.command("show", "Shows information about punishments", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def show(ctx: lightbulb.context.SlashContext):
    config = await PunishmentConfig.objects.get_or_none(guild=ctx.guild_id)
    songs = PunishmentSong.objects.filter(guild=ctx.guild_id)
    punishments: Dict[int, Dict[int, int]] = ctx.bot.d.punishments.get(ctx.guild_id, {})

    if config is None or config.channel is None:
        channel = "Not Configured"
    else:
        channel = f"<#{config.channel}>"

    song_list = []
    async for song in songs.iterate():
        song_list.append(f"🔹[{song.name}]({song.url})")

    if not song_list:
        song_list.append('No Songs configured')

    now = int(time.time())
    punishment_list = []
    for user_id, expire in punishments.items():
        remaining = expire - now
        punishment_list.append(f"🔹<@{user_id}> - {remaining}")

    if not punishment_list:
        punishment_list.append('No punishments active')

    await ctx.respond(
        hikari.Embed(
            description=f"Punishment Channel: {channel}",
            color=hikari.Colour(0x2ECC71)
        ).add_field(
            name="Songs", value="\n".join(song_list)
        ).add_field(
            name="Punishments", value="\n".join(punishment_list)
        )
    )


@punish_group.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("url", "The URL of the clip")
@lightbulb.option("name", "The name of the clip to add")
@lightbulb.command("add-song", "Adds a new song to play in the punishment channel", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def add_song(ctx: lightbulb.context.SlashContext, name: str, url: str):
    song = await PunishmentSong.objects.get_or_none(guild=ctx.guild_id, name=name.lower())

    if song is not None:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Punishment song with name {name} already exists",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    result = await lavalink.auto_search_tracks(url)

    if not result:
        await ctx.respond(
           embed=hikari.Embed(
                description="No results found for your query",
                color=hikari.Colour(0xd32f2f)
            )
        )

    result = result[0]

    await PunishmentSong.objects.create(guild=ctx.guild_id, name=name.lower(), url=result.uri)

    await ctx.respond(
        hikari.Embed(
            description=f"Punishment song {name} added!\n"
                        f"🔹[{result.title}]({result.uri})",
            color=hikari.Colour(0x2ECC71)
        )
    )


@punish_group.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("name", "The name of the clip to add")
@lightbulb.command("rem-song", "Removes a song from the punishment list", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def remove_song(ctx: lightbulb.context.SlashContext, name: str):
    song = await PunishmentSong.objects.get_or_none(guild=ctx.guild_id, name=name.lower())

    if song is None:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Punishment song with name {name} does not exist",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    await song.delete()

    await ctx.respond(
        hikari.Embed(
            description=f"Punishment song {name} deleted!",
            color=hikari.Colour(0x2ECC71)
        )
    )


@punish_group.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("seconds", "The time to punish the user", type=int, min_value=5, max_value=MAX_PUNISHMENT_TIME)
@lightbulb.option("user", "The user to punish", type=hikari.User)
@lightbulb.command("user", "Adds a punishment for the specified user", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def punish_user(ctx: lightbulb.context.SlashContext, user: hikari.InteractionMember, seconds: int):
    config = await PunishmentConfig.objects.get_or_none(guild=ctx.guild_id)
    if config is None or config.channel is None:
        await ctx.respond(
           embed=hikari.Embed(
                description="Punishment channel config is not set!",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    if ctx.guild_id not in ctx.bot.d.punishments:
        ctx.bot.d.punishments[ctx.guild_id] = {}

    ctx.bot.d.punishments[ctx.guild_id][user.id] = int(time.time()) + seconds

    # Set a task to remove punishment?

    await ctx.respond(
        hikari.Embed(
            description=f"Punishing <@{user.id}> for {seconds}s!",
            color=hikari.Colour(0x2ECC71)
        )
    )

    # Check if the user is in a voice channel now, punish them!
    if ctx.bot.cache.get_voice_state(ctx.guild_id, user.id) is None:
        return

    try:
        await ctx.bot.rest.edit_member(ctx.guild_id, user.id, voice_channel=config.channel)
    except hikari.ForbiddenError:
        pass


@punish_group.child
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("user", "The user to clear", type=hikari.User, required=False)
@lightbulb.command("clear", "Clears punishments for all users, or the specified user", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def clear_punishment(ctx: lightbulb.context.SlashContext, user: Optional[hikari.InteractionChannel] = None):
    if user is None:
        ctx.bot.d.punishments[ctx.guild_id] = {}

        await ctx.respond(
            hikari.Embed(
                description="Cleared All Punishments!",
                color=hikari.Colour(0x2ECC71)
            )
        )
        return

    if user.id not in ctx.bot.d.punishments[ctx.guild_id]:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"User <@{user.id}> is not currently punished.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    del ctx.bot.d.punishments[ctx.guild_id][user.id]

    await ctx.respond(
            hikari.Embed(
                description=f"Cleared punishments for <@{user.id}>!",
                color=hikari.Colour(0x2ECC71)
            )
        )


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_server_update(event: hikari.VoiceStateUpdateEvent):
    # Ignore events from myself
    if event.state.user_id == plugin.bot.get_me().id:
        return

    config = await PunishmentConfig.objects.get_or_none(guild=event.guild_id)
    # IF punishment hasn't been setup
    if config is None or config.channel is None:
        return

    voice: LavalinkVoice = plugin.bot.voice.connections.get(event.guild_id)
    punishments = plugin.bot.d.punishments.get(event.guild_id, {})

    # User Entering the punishment channel
    if event.state.channel_id == config.channel:
        # If sunbot is already busy, we can't do anything
        if voice:
            return

        songs = await PunishmentSong.objects.filter(guild=event.guild_id).all()
        if not songs:
            return

        voice = await LavalinkVoice.connect(
            event.guild_id,
            config.channel,
            plugin.bot,
            plugin.bot.lavalink,
            (config.channel, plugin.bot.rest),
        )

        song: PunishmentSong = random.choice(songs)
        player = voice.player

        result = await player.node.get_tracks(song.url)
        await player.play(result.tracks[0])

    # User been punished entering a non-punishment channel
    elif event.state.user_id in punishments:

        # Check if their punishment is over
        until = punishments[event.state.user_id]
        if until - int(time.time()) <= 0:
            del plugin.bot.d.punishments[event.guild_id][event.state.user_id]
            return

        try:
            await plugin.bot.rest.edit_member(event.guild_id, event.state.user_id, voice_channel=config.channel)
        except hikari.ForbiddenError:
            pass
    # User leaving the punishment channel
    elif event.old_state is not None and event.old_state.channel_id == config.channel:
        if voice and voice.channel_id == config.channel:
            if len(plugin.bot.cache.get_voice_states_view_for_channel(event.guild_id, config.channel)) == 1:
                await voice.disconnect()


async def track_end_event(event: lavalink.TrackEndEvent):

    player = event.player

    # If we are not in a voice channel
    if not player:
        return

    # IF punishment hasn't been setup
    config = await PunishmentConfig.objects.get_or_none(guild=player.guild_id)
    if config is None or config.channel is None:
        return

    # Or we are not in the punishment channel
    if player.channel_id != config.channel:
        return

    # Or if we have no songs to play
    songs = await PunishmentSong.objects.filter(guild=player.guild_id).all()
    if not songs:
        return

    song: PunishmentSong = random.choice(songs)
    result = await player.node.get_tracks(song.url)
    await player.play(result.tracks[0])


def load(bot: lightbulb.BotApp) -> None:

    if lavalink is None:
        logger.warning('Not loading Punishment plugin as lavalink is not setup')
        return

    bot.add_plugin(plugin)
    bot.lavalink.add_event_hook(track_end_event, event=lavalink.TrackEndEvent)

    # Setup temp storage of punishments
    bot.d.punishments: Dict[int, Dict[int, int]] = {}


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
