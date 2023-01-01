import lightbulb
import hikari
from time import time
from datetime import timedelta
from psutil import Process
from hikari import __version__ as hikari_version
from lightbulb import __version__ as lightbulb_version
from platform import python_version
from sunbot import __version__


plugin = lightbulb.Plugin("Info")


@plugin.command
@lightbulb.command("info", "Displays information about the bot")
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def ping(ctx: lightbulb.context.SlashContext) -> None:
    proc = Process()
    with proc.oneshot():
        uptime = timedelta(seconds=time() - proc.create_time())

    me = plugin.bot.get_me()
    embed = hikari.Embed(
        title=f"{me.username}'s Information",
        color=hikari.Colour(0xF1C40F)
    )
    embed.set_thumbnail(me.avatar_url)
    embed.add_field("Language", f"Python {python_version()}")
    embed.add_field("Bot Version", __version__)
    embed.add_field("Library", f"hikari-py v{hikari_version}")
    embed.add_field("Command Handler", f"lightbulb v{lightbulb_version}")
    embed.add_field("Uptime", str(uptime))
    embed.add_field("Author", "<@116586345115287558>")
    await ctx.respond(embed)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
