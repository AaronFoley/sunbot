from random import randint
import lightbulb
import hikari


plugin = lightbulb.Plugin("ping")


@plugin.command
@lightbulb.command("ping", "Displays the ping/latency of the bot", ephemeral=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def ping(ctx: lightbulb.context.SlashContext) -> None:
    await ctx.respond(
        embed=hikari.Embed(
            description=f"Pong! `{round(ctx.bot.heartbeat_latency * 1000, 2)}ms`",
            color=randint(0, 0xffffff)
        )
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
