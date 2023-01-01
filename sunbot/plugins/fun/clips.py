import lightbulb
import hikari
import lavaplayer
from sunbot.config import CONFIG
from sunbot.bot import lavalink


plugin = lightbulb.Plugin("Clips")


@plugin.command
@lightbulb.option("clip", "The clip to play")
@lightbulb.command("clip", "Plays a short audio clip in the voice channel you are in", pass_options=True, ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def voiceclip(ctx: lightbulb.context.SlashContext, clip: str) -> None:
    clip = clip.lower()

    if clip not in CONFIG.clips:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Unknown clip: {clip}",
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

    await ctx.respond(f"Playing clip: {clip}")

    await ctx.bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
    await lavalink.wait_for_connection(ctx.guild_id)

    clip_path = CONFIG.clips.get(clip).path
    clip_seek = CONFIG.clips.get(clip).seek

    result = await lavalink.auto_search_tracks(clip_path)

    # Store the track here as we can't get good information from the lavaplayer library
    plugin.bot.d.clip_track = result[0]

    await lavalink.play(ctx.guild_id, result[0])
    if clip_seek:
        await lavalink.seek(ctx.guild_id, clip_seek)


@lavalink.listen(lavaplayer.TrackEndEvent)
async def track_end_event(event: lavaplayer.TrackEndEvent):

    if 'clip_track' not in plugin.bot.d:
        return

    # If this is the clip that was last played, leave VC
    if event.track.identifier == plugin.bot.d.clip_track.identifier:
        await plugin.bot.update_voice_state(event.guild_id, None)
        del plugin.bot.d.clip_track


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
