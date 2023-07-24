import lightbulb
import hikari
import lavaplay
import logging
from datetime import timedelta
from lavaplay.player import Player
from lightbulb.ext import tasks
from sunbot.bot import lavalink

logger = logging.getLogger(__name__)
plugin = lightbulb.Plugin("Music")


@plugin.command()
@lightbulb.option(name="query", description="query to search", required=True)
@lightbulb.command(name="play", description="Play command", pass_options=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def play_command(ctx: lightbulb.context.Context, query: str):
    """ Plays music """

    if not (voice_state := ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author.id)):
        await ctx.respond(
           embed=hikari.Embed(
                description="Connect to a voice channel first.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    channel_id = voice_state.channel_id

    bot_voice_state = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.bot.get_me().id)
    if bot_voice_state and bot_voice_state.channel_id != channel_id:
        await ctx.respond(
           embed=hikari.Embed(
                description="Sunbot is already busy in another voice channel ~ sorry!.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    elif not bot_voice_state:
        lavalink.create_player(ctx.guild_id)
        await ctx.bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)

    player = lavalink.get_player(ctx.guild_id)
    position = len(player.queue)
    result = await lavalink.auto_search_tracks(query)
    if not result:
        await ctx.respond(
           embed=hikari.Embed(
                description="No results found for your query",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    elif isinstance(result, lavaplay.TrackLoadFailed):
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Track load failed, try again later.\n ```{result.message}```",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    elif isinstance(result, lavaplay.PlayList):
        player.add_to_queue(ctx.guild_id, result.tracks, ctx.author.id)
        tracks = []
        total_duration = 0
        for track in result.tracks:
            tracks.append(f"🔹[{track.title}]({track.uri})")
            total_duration += track.length

        tracks = "\n".join(tracks)
        duration = timedelta(milliseconds=total_duration)
        await ctx.respond(hikari.Embed(
            description=f"{tracks}\n"
                        f"Position: `{position}-{position + len(result.tracks)}` | Duration: `{str(duration)}`",
            color=hikari.Colour(0x2ECC71)
        ).set_author(name="Added Playlist to Queue", icon=ctx.author.avatar_url))
        return

    duration = timedelta(milliseconds=result[0].length)
    await player.play(result[0], ctx.author.id)
    await ctx.respond(hikari.Embed(
        description=f"🔹[{result[0].title}]({result[0].uri})\n"
                    f"Position: `{position}` | Duration: `{str(duration)}`",
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Added to Queue", icon=ctx.author.avatar_url))


async def is_player_paused(player: Player) -> bool:
    """ Given a player, check if it is paused """

    resp = await player.rest.get_player(
        session_id=player.node.session_id,
        guild_id=player.guild_id
    )
    return resp.get('paused', False)


@plugin.command()
@lightbulb.command(name="pause", description="Pauses playing music")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def pause_command(ctx: lightbulb.context.Context):
    player = lavalink.get_player(ctx.guild_id)
    if not player or not player.queue:
        await ctx.respond(
           embed=hikari.Embed(
                description="No tracks are currently playing.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    
    if await is_player_paused(player):
        await ctx.respond(
           embed=hikari.Embed(
                description="It's already paused! :rage:",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    await player.pause(True)
    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Paused the Music", icon=ctx.author.avatar_url))


@plugin.command()
@lightbulb.command(name="resume", description="Resumes playing music")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def resume_command(ctx: lightbulb.context.Context):
    player = lavalink.get_player(ctx.guild_id)

    if not player or not player.queue:
        await ctx.respond(
           embed=hikari.Embed(
                description="No tracks are currently playing.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    if not await is_player_paused(player):
        await ctx.respond(
           embed=hikari.Embed(
                description="It's already playing! :rage:",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    await player.pause(False)
    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Resumed the Music", icon=ctx.author.avatar_url))


@plugin.command()
@lightbulb.command(name="skip", description="Skip the current song")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def skip_command(ctx: lightbulb.context.Context):
    player = lavalink.get_player(ctx.guild_id)
    if not player or not player.queue:
        await ctx.respond(
           embed=hikari.Embed(
                description="No tracks are currently playing.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    current_track = player.queue[0]
    await player.skip()
    await ctx.respond(hikari.Embed(
        description=f"🔹[{current_track.title}]({current_track.uri})",
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Skipped the current Song", icon=ctx.author.avatar_url))


@plugin.command()
@lightbulb.command(name="queue", description="Displays the current songs in the queue")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def queue_command(ctx: lightbulb.context.Context):
    player = lavalink.get_player(ctx.guild_id)
    if not player or not player.queue:
        await ctx.respond(
           embed=hikari.Embed(
                description="No tracks are currently playing.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    song_queue = []
    now_playing = player.queue[0]

    for track in player.queue[1:]:
        duration = timedelta(milliseconds=track.length)
        song_queue.append(f"🔹`{str(duration)}` [{track.title}]({track.uri}) [<@{track.requester}>]")

    if not song_queue:
        song_queue = ['Nothing queued']

    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).add_field(
        name="Now Playing", value=f"[{now_playing.title}]({now_playing.uri})"
    ).add_field(
        name="Queue", value="\n".join(song_queue)
    ))


@plugin.command()
@lightbulb.command(name="nowplaying", description="Displays information about the song that is currently playing")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def nowplaying_command(ctx: lightbulb.context.Context):
    player = lavalink.get_player(ctx.guild_id)
    if not player or not player.queue:
        await ctx.respond(
           embed=hikari.Embed(
                description="No tracks are currently playing.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    now_playing = player.queue[0]
    duration = timedelta(milliseconds=now_playing.length)
    await ctx.respond(hikari.Embed(
        title="Now Playing",
        description=f"[{now_playing.title}]({now_playing.uri})",
        color=hikari.Colour(0x2ECC71),
    ).add_field(
        name="Requsted By", value=f"<@{now_playing.requester}>"
    ).add_field(
        name="Author", value=now_playing.author
    ).add_field(
        name="Duration", value=str(duration)
    ).add_field(
        name="Source", value=now_playing.source_name
    ))


@plugin.command()
@lightbulb.command(name="stop", description="Stop command")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def stop_command(ctx: lightbulb.context.Context):  
    await plugin.bot.update_voice_state(ctx.guild_id, None)
    player = lavalink.get_player(ctx.guild_id)
    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Stopped playing music", icon=ctx.author.avatar_url))


@tasks.task(s=60, auto_start=True)
async def disconnect_if_empty():
    """ Leave the voice channel if there are no other users in the channel """

    for player in lavalink.get_players():
        bot_voice_state = plugin.bot.cache.get_voice_state(player.guild_id, plugin.bot.get_me().id)
        if not bot_voice_state:
            continue

        voice_states = plugin.bot.cache.get_voice_states_view_for_channel(player.guild_id, bot_voice_state.channel_id)
        if len(voice_states) == 1:
            logger.info(f'Leaving voice channel {bot_voice_state.channel_id} in guild {player.guild_id} as it is empty')
            await plugin.bot.update_voice_state(player.guild_id, None)


def load(bot: lightbulb.BotApp) -> None:
    if lavalink is None:
        logger.warning('Not loading Music plugin as lavalink is not setup')
        return

    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
