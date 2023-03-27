import lightbulb
from lightbulb.utils import permissions
import hikari
import lavaplayer
from datetime import timedelta
from sunbot.bot import lavalink
from sunbot.db.models.clip import Clip


plugin = lightbulb.Plugin("Clips")


MAX_CLIP_LENGTH_SECONDS = 20


@plugin.command
@lightbulb.command("clip", "Commands related to playing and adding clips")
@lightbulb.implements(lightbulb.commands.SlashCommandGroup)
async def clip_group(ctx: lightbulb.context.SlashContext):
    pass


@clip_group.child
@lightbulb.option("seek", "Time in seconds to skip in the clip", type=float, min_value=0, default=0, required=False)
@lightbulb.option("url", "The URL of the clip")
@lightbulb.option("name", "The name of the clip to add")
@lightbulb.command("add", "Adds a new clip", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def add_clip(ctx: lightbulb.context.SlashContext, name: str, url: str, seek: float = 0):
    # Workout if a clip with this name already exists
    clip = await Clip.objects.get_or_none(guild=ctx.guild_id, name=name.lower())

    if clip is not None:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Clip with name {name} already exists",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    # Ensure the clip length is not too long, taking into account the seek duration
    result = await lavalink.auto_search_tracks(url)

    if not result:
        await ctx.respond(
           embed=hikari.Embed(
                description="No results found for your query",
                color=hikari.Colour(0xd32f2f)
            )
        )
    
    result = result[0]
    seek_ms = int(seek * 1000)
    duration = timedelta(milliseconds=result.length)

    if seek_ms > result.length:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"🔹[{result.title}]({result.uri})\n"
                            f"Seek seconds `{seek}` is longer than the duration of the clip `{duration}`",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    if result.length - seek_ms > (MAX_CLIP_LENGTH_SECONDS * 1000):
        await ctx.respond(
           embed=hikari.Embed(
                description=f"🔹[{result.title}]({result.uri})\n"
                            f"Clip Duration: `{str(duration)}` is longer than max clip length: `{MAX_CLIP_LENGTH_SECONDS}`",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    await Clip.objects.create(guild=ctx.guild_id, author=ctx.author.id, name=name.lower(), url=result.uri, seek=seek_ms)

    await ctx.respond(
        hikari.Embed(
            description=f"Clip {name} Created!\n"
                        f"🔹[{result.title}]({result.uri})",
            color=hikari.Colour(0x2ECC71)
        )
    )


@clip_group.child
@lightbulb.option("name", "The clip to play")
@lightbulb.command("play", "Plays a short audio clip in the voice channel you are in", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def play_clip(ctx: lightbulb.context.SlashContext, name: str):

    clip = await Clip.objects.get_or_none(guild=ctx.guild_id, name=name.lower())

    if clip is None:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Unknown clip: {name}",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    if not (voice_state := ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author.id)):
        await ctx.respond(
           embed=hikari.Embed(
                description="Connect to a voice channel first.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    channel_id = voice_state.channel_id

    if ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.bot.get_me().id):
        await ctx.respond(
           embed=hikari.Embed(
                description="Sunbot is already busy in another voice channel ~ sorry!.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    await ctx.respond(f"Playing clip: {name}")

    await ctx.bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
    await lavalink.wait_for_connection(ctx.guild_id)

    result = await lavalink.auto_search_tracks(clip.url)

    # Store the track here as we can't get good information from the lavaplayer library
    plugin.bot.d.clips_playing[ctx.guild_id] = result[0]

    await lavalink.play(ctx.guild_id, result[0])
    if clip.seek:
        await lavalink.seek(ctx.guild_id, clip.seek)


@clip_group.child
@lightbulb.command("list", "Lists the clips that are defined", ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def list_clips(ctx: lightbulb.context.SlashContext):

    # If this user is an admin, list all the clips
    if permissions.permissions_for(ctx.member) & hikari.Permissions.ADMINISTRATOR:
        clips = Clip.objects.filter(guild=ctx.guild_id)
    # Otherwise, just list the clips created by this user
    else:
        clips = Clip.objects.filter(guild=ctx.guild_id, author=ctx.member.id)

    clip_output = []
    async for clip in clips.iterate():
        clip_output.append(f"🔹[{clip.name}]({clip.url}) ({clip.seek}) [<@{clip.author}>]")

    await ctx.respond(hikari.Embed(
        color=hikari.Colour(0x2ECC71)
    ).add_field(
        name="Clips", value="\n".join(clip_output)
    ))


@clip_group.child
@lightbulb.option("name", "The clip to delete")
@lightbulb.command("delete", "Deletes a clip", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashSubCommand)
async def delete_clip(ctx: lightbulb.context.SlashContext, name: str):

    clip = await Clip.objects.get_or_none(guild=ctx.guild_id, name=name.lower())

    if clip is None:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Unknown clip: {name}",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    # If the user doesn't own this clip, then they can't delete it
    if clip.author != ctx.member.id or not (permissions.permissions_for(ctx.member) & hikari.Permissions.ADMINISTRATOR):
        await ctx.respond(
           embed=hikari.Embed(
                description=f"You do not have permission to delete this clip: {name}",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    await Clip.objects.delete(guild=ctx.guild_id, name=name.lower())
    await ctx.respond(
        hikari.Embed(
            description=f"Clip {name} Deleted!",
            color=hikari.Colour(0x2ECC71)
        )
    )


@lavalink.listen(lavaplayer.TrackEndEvent)
async def track_end_event(event: lavaplayer.TrackEndEvent):

    if event.guild_id not in plugin.bot.d.clips_playing:
        return

    playing_track = plugin.bot.d.clips_playing[event.guild_id]

    # If this is the clip that was last played, leave VC
    if event.track.identifier == playing_track.identifier:
        await plugin.bot.update_voice_state(event.guild_id, None)
        del plugin.bot.d.clips_playing[event.guild_id]


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

    # Create the in-memory storage of clips playing
    bot.d.clips_playing = {}


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
