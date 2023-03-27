import logging
import random
import time
from datetime import timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict

import hikari
import lightbulb
from hikari import Message
from lightbulb.ext import tasks
import openai

from sunbot.config import CONFIG

logger = logging.getLogger(__name__)
plugin = lightbulb.Plugin("OpenAI")

openai.api_key = CONFIG.openai.api_key


@dataclass
class OpenAiContext:
    """ Holds the context for auto reply feature
        Attributes:
            last_trigger (int): The unix timestamp of the last time a message was triggered
            target_message (Message): The message that caused triggered the response
            messages (List[messages]): List of messages that happened while collecting context
            last_context (int): unix timestamp of the last time we collected a context message
    """

    last_trigger: int = 0

    target_message: Optional[Message] = None
    messages: List[Message] = field(default_factory=list)
    last_context: int = 0

    def reset(self):
        self.target_message = None
        self.messages = None
        self.last_context = 0


@tasks.task(s=10, auto_start=True)
async def auto_repsonse():
    """ Do the auto response """

    all_context: Dict[int, OpenAiContext] = plugin.bot.d.openai

    now = time.time()

    for _, octx in all_context.items():
        if octx.target_message is None:
            return

        # If we are below both the timeout and last poll phase then wait some more
        if now < (octx.last_trigger + CONFIG.openai.auto_context_timeout):
            if now < (octx.last_context + CONFIG.openai.auto_context_poll):
                return

        logger.info(f'Generating reponse to {octx.target_message.id}')

        prompt = CONFIG.openai.auto_prompt

        for msg in octx.messages:
            prompt += f"\n{msg.author.username}: {msg.content}"

        try:
            completion = await openai.Completion.acreate(
                model=CONFIG.openai.auto_completions_model,
                max_tokens=CONFIG.openai.auto_max_tokens,
                prompt=prompt
            )
            resp = completion.choices[0].text
            await plugin.bot.rest.create_message(octx.target_message.channel_id, resp)
        except openai.InvalidRequestError as e:
            logger.exception(f"Failed to automatically respond due to OpenAi Error: {e}")
            pass

        octx.reset()


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message(event: hikari.GuildMessageCreateEvent):
    if event.is_bot or event.content is None:
        return

    octx: OpenAiContext = plugin.bot.d.openai[event.guild_id]
    if octx.target_message is None:
        if len(event.message.content.split()) < CONFIG.openai.auto_min_length:
            return

        if octx.last_trigger > (int(time.time()) - CONFIG.openai.auto_cooldown):
            return

        if not random.random() < CONFIG.openai.auto_trigger_chance:
            return

        logger.info(f'Triggered Automatic response on message: {event.message_id}: {event.message.content}')

        octx.last_trigger = int(time.time())
        octx.last_context = octx.last_trigger
        octx.target_message = event.message

        cutoff = event.message.created_at - timedelta(seconds=CONFIG.openai.auto_pre_context_time)
        msgs = await plugin.bot.rest.fetch_messages(event.channel_id, after=cutoff)
        octx.messages.extend(msgs)

    else:
        # In a different channel, not part of the "Conversation"
        if event.channel_id != octx.target_message.channel_id:
            return

        octx.messages.append(event.message)
        octx.last_context = int(time.time())


@plugin.command
@lightbulb.add_cooldown(CONFIG.openai.command_cooldown, 1, lightbulb.UserBucket)
@lightbulb.option("prompt", "The Prompt to send to ChatGPT")
@lightbulb.command("askgpt", "Ask a question to OpenAI", pass_options=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def askgpt(ctx: lightbulb.context.SlashContext, prompt: str):
    try:
        completion = await openai.Completion.acreate(
            model=CONFIG.openai.auto_completions_model,
            max_tokens=CONFIG.openai.auto_max_tokens,
            prompt=prompt
        )
    except openai.InvalidRequestError as e:
        await ctx.respond(
           embed=hikari.Embed(
                description=f"Failed to send request to ChatGPT: {e}",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    resp = completion.choices[0].text
    await ctx.respond(resp)


@plugin.command
@lightbulb.add_cooldown(CONFIG.openai.command_cooldown, 1, lightbulb.UserBucket)
@lightbulb.option("size", "The size of the image to generate", default="1024x1024", choices=["256x256", "512x512", "1024x1024"])
@lightbulb.option("number", "Number of images to generate", default=4, type=int, required=False)
@lightbulb.option("prompt", "The Prompt to send to ChatGPT")
@lightbulb.command("genimage", "Generates an image using OpenAI", pass_options=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def genimage(ctx: lightbulb.context.SlashContext, prompt: str, number: int, size: str):
    resp = await ctx.respond('Generating images ... please wait')

    try:
        images = await openai.Image.acreate(
            n=number,
            prompt=prompt,
            size=size
        )
    except openai.InvalidRequestError as e:
        await resp.edit(
           embed=hikari.Embed(
                description=f"Failed to generate images: {e}",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    for image in images.data:
        msg = await resp.message()
        attachments = msg.attachments + [image['url']]
        await msg.edit(attachments=attachments)

    await resp.edit(content="Images Generated!")


def load(bot: lightbulb.BotApp) -> None:
    if not CONFIG.openai or not CONFIG.openai.api_key:
        logger.warning('Not loading OpenAI plugin as openai.api_key is not defined in config')
        return

    bot.add_plugin(plugin)
    bot.d.openai: Dict[int, OpenAiContext] = defaultdict(lambda: OpenAiContext())


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
