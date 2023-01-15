import re
import random
import lightbulb
import hikari


plugin = lightbulb.Plugin("Dad")


PATTERN = re.compile(r"\bi(?:'| +a|’)?m +([\w ]*)", re.IGNORECASE)


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message(event: hikari.GuildMessageCreateEvent):
    if event.is_bot:
        return

    if not (match := re.search(PATTERN, event.content)):
        return
   
    name = match.group(1)
    if not name or len(name) > 32:
        return

    if random.random() < 0.8:
        return

    await plugin.bot.rest.create_message(event.channel_id, f"Hi {name}, I'm Sunbot!", reply=event.message_id, mentions_reply=True)

    try:
        await plugin.bot.rest.edit_member(event.guild_id, event.author_id, nickname=name)
    except hikari.ForbiddenError:
        pass


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
