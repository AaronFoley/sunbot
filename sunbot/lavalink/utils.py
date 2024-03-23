import hikari
import lightbulb
from sunbot.lavalink.voice import LavalinkVoice


async def join_voice(ctx: lightbulb.Context) -> hikari.Snowflake | None:
    """ Helper function to join the bot to voice """
    if not ctx.guild_id:
        return None

    # Check the user is in a voice channel
    voice_state = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author.id)
    if not voice_state or not voice_state.channel_id:
        await ctx.respond(
           embed=hikari.Embed(
                description="Connect to a voice channel first.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return None

    channel_id = voice_state.channel_id
    voice = ctx.bot.voice.connections.get(ctx.guild_id)

    # Check if we are already in another channel
    if voice and voice.channel_id != channel_id:
        await ctx.respond(
            embed=hikari.Embed(
                description="Sunbot is already busy in another voice channel ~ sorry!.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return None

    # Otherwise connect
    if not voice:
        voice = await LavalinkVoice.connect(
            ctx.guild_id,
            channel_id,
            ctx.bot,
            ctx.bot.lavalink,
            (ctx.channel_id, ctx.bot.rest),
        )

    return channel_id


@lightbulb.Check
async def check_in_voice(ctx: lightbulb.Context) -> bool:
    voice = ctx.bot.voice.connections.get(ctx.guild_id)
    if not voice:
        await ctx.respond(
           embed=hikari.Embed(
                description="Sunbot is currently not in a voice channel - use /play to play some music",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return False
    return True


@lightbulb.Check
async def check_music_queued(ctx: lightbulb.Context) -> bool:
    voice: LavalinkVoice = ctx.bot.voice.connections.get(ctx.guild_id)
    if not voice and (voice.player.queue or voice.player.current):
        await ctx.respond(
           embed=hikari.Embed(
                description="No tracks are currently playing.",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return False
    return True
