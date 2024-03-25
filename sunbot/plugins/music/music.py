import lightbulb
import hikari
import logging
import re
import lavalink
from datetime import timedelta
from lightbulb.ext import tasks
from sunbot.lavalink.voice import LavalinkVoice
from sunbot.lavalink.utils import join_voice, check_in_voice, check_music_queued


logger = logging.getLogger(__name__)
plugin = lightbulb.Plugin("Music")


@plugin.command()
@lightbulb.option(name="query", description="query to search", required=True)
@lightbulb.command(name="play", description="Play command", pass_options=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def play_command(ctx: lightbulb.context.Context, query: str):
    """ Plays music """

    if not await join_voice(ctx):
        return

    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    player = voice.player

    # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
    query = query.strip('<>')

    # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
    url_rx = re.compile(r'https?://(?:www\.)?.+')
    if not url_rx.match(query):
        query = f'ytsearch:{query}'

    # Get the results for the query from Lavalink.
    results = await player.node.get_tracks(query)

    if not results or not results.tracks:
        await ctx.respond(
           embed=hikari.Embed(
                description="No results found for your query",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    description: str
    action: str
    position: int = len(player.queue)

    if results.load_type == lavalink.LoadType.PLAYLIST:
        track_details = []
        total_duration = 0
        for track in results.tracks:
            player.add(requester=ctx.author.id, track=track)
            track_details.append(f"🔹[{track.title}]({track.uri})")
            total_duration += track.duration

        action = 'Added Playlist to Queue'
        duration = timedelta(milliseconds=total_duration)

        description = f"{'\n'.join(track_details[:10])}\n"
        if len(track_details) > 10:
            description += f'+ {len(track_details) - 10} more\n'
        description += f"Position: `{position}-{position + len(results.tracks)}` | Duration: `{str(duration)}`"
    else:
        track = results.tracks[0]
        player.add(requester=ctx.author.id, track=track)
        action = 'Added to Queue'
        duration = timedelta(milliseconds=track.duration)
        description = (
            f"🔹[{track.title}]({track.uri})\n"
            f"Position: `{position}` | Duration: `{str(duration)}`"
        )

    if not player.is_playing:
        await player.play()

    await ctx.respond(hikari.Embed(
        description=description,
        color=hikari.Colour(0x2ECC71)
    ).set_author(name=action, icon=ctx.author.avatar_url))


@plugin.command()
@lightbulb.add_checks(check_in_voice, check_music_queued)
@lightbulb.command(name="pause", description="Pauses playing music")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def pause_command(ctx: lightbulb.context.Context):
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    player = voice.player

    if player.paused:
        await ctx.respond(
           embed=hikari.Embed(
                description="It's already paused! :rage:",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    await player.set_pause(True)
    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Paused the Music", icon=ctx.author.avatar_url))


@plugin.command()
@lightbulb.add_checks(check_in_voice, check_music_queued)
@lightbulb.command(name="resume", description="Resumes playing music")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def resume_command(ctx: lightbulb.context.Context):
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    player = voice.player

    if not player.paused:
        await ctx.respond(
           embed=hikari.Embed(
                description="It's already playing! :rage:",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    await player.set_pause(False)
    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Resumed the Music", icon=ctx.author.avatar_url))


@plugin.command()
@lightbulb.add_checks(check_in_voice, check_music_queued)
@lightbulb.command(name="skip", description="Skip the current song")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def skip_command(ctx: lightbulb.context.Context):
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    player = voice.player
    current_track = player.current
    await player.skip()
    now_playing = player.current
    await ctx.respond(
        hikari.Embed(
            description=f"[{current_track.title}]({current_track.uri})",
            color=hikari.Colour(0x2ECC71)
        ).set_author(
            name="Skipped the current Song", icon=ctx.author.avatar_url
        ).add_field(
            name="Now Playing", value=f"[{now_playing.title}]({now_playing.uri})"
        )
    )


@plugin.command()
@lightbulb.add_checks(check_in_voice, check_music_queued)
@lightbulb.command(name="queue", description="Displays the current songs in the queue")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def queue_command(ctx: lightbulb.context.Context):
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    player = voice.player

    song_queue = []
    now_playing = player.current

    for track in player.queue[:10]:
        duration = timedelta(milliseconds=track.duration)
        song_queue.append(f"🔹`{str(duration)}` [{track.title}]({track.uri}) [<@{track.requester}>]")

    if len(player.queue) > 10:
        song_queue += f'+ {len(player.current) - 10} more\n'

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
@lightbulb.add_checks(check_in_voice, check_music_queued)
@lightbulb.command(name="nowplaying", description="Displays information about the song that is currently playing")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def nowplaying_command(ctx: lightbulb.context.Context):
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    player = voice.player

    now_playing = player.current
    duration = timedelta(milliseconds=now_playing.duration)
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
@lightbulb.add_checks(check_in_voice)
@lightbulb.command(name="clear", description="Clears the song queue")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def clear_command(ctx: lightbulb.context.Context):
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    voice.player.queue.clear()
    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Cleared the Queue", icon=ctx.author.avatar_url))


@plugin.command()
@lightbulb.add_checks(check_in_voice)
@lightbulb.command(name="stop", description="Stops playing music and leaves the voice channel")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def stop_command(ctx: lightbulb.context.Context):
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    await voice.disconnect()
    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).set_author(name="Stopped playing music", icon=ctx.author.avatar_url))


@tasks.task(s=60, auto_start=True)
async def disconnect_if_empty():
    """ Leave the voice channel if there are no other users in the channel """

    for _, player in plugin.bot.lavalink.players.items():
        voice = plugin.bot.voice.connections.get(player.guild_id)
        if not voice:
            continue
        voice_states = plugin.bot.cache.get_voice_states_view_for_channel(player.guild_id, voice.channel_id)
        if len(voice_states) == 1:
            logger.info(f'Leaving voice channel {voice.channel_id} in guild {player.guild_id} as it is empty')
            await voice.disconnect()


def load(bot: lightbulb.BotApp) -> None:
    if bot.lavalink is None:
        logger.warning('Not loading Music plugin as lavalink is not setup')
        return

    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
