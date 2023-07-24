import logging
import random
import time
from datetime import timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict

import aiohttp
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
        self.messages = list()
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
        if now < (octx.last_trigger + CONFIG.openai.auto.context_timeout):
            if now < (octx.last_context + CONFIG.openai.auto.context_poll):
                return

        logger.info(f'Generating reponse to {octx.target_message.id}')

        prompt = CONFIG.openai.auto.prompt

        for msg in octx.messages:
            prompt += f"\n{msg.author.username}: {msg.content}"

        try:
            completion = await openai.Completion.acreate(
                model=CONFIG.openai.auto.completions_model,
                max_tokens=CONFIG.openai.auto.max_tokens,
                prompt=prompt
            )
            resp = completion.choices[0].text
            await plugin.bot.rest.create_message(octx.target_message.channel_id, resp)
        except openai.OpenAIError as e:
            logger.exception(f"Failed to automatically respond due to OpenAi Error: {e}")
            pass

        octx.reset()


@plugin.listener(hikari.GuildMessageCreateEvent)
async def auto_response_on_message(event: hikari.GuildMessageCreateEvent):
    """ Handler to listen for messages that could be automatically replied too """
    if event.is_bot or event.content is None:
        return
    
    message: hikari.Message = event.message
    me: hikari.OwnUser = plugin.bot.get_me()
    
    # If this message is a reply to us, or mentions us, then we aren't interested
    if (message.type == hikari.MessageType.REPLY and message.referenced_message.author.id == me.id) or \
       (me.id in message.user_mentions_ids):
        return

    octx: OpenAiContext = plugin.bot.d.openai[event.guild_id]
    if octx.target_message is None:
        if len(message.content.split()) < CONFIG.openai.auto.min_length:
            return

        if octx.last_trigger > (int(time.time()) - CONFIG.openai.auto.cooldown):
            return

        if not random.random() < CONFIG.openai.auto.trigger_chance:
            return

        logger.info(f'Triggered Automatic response on message: {event.message_id}: {message.content}')

        octx.last_trigger = int(time.time())
        octx.last_context = octx.last_trigger
        octx.target_message = message

        cutoff = message.created_at - timedelta(seconds=CONFIG.openai.auto.pre_context_time)
        msgs = await plugin.bot.rest.fetch_messages(event.channel_id, after=cutoff)
        octx.messages.extend(msgs)

    else:
        # In a different channel, not part of the "Conversation"
        if event.channel_id != octx.target_message.channel_id:
            return

        octx.messages.append(message)
        octx.last_context = int(time.time())


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_mention_me(event: hikari.GuildMessageCreateEvent):

    if event.is_bot or event.content is None:
        return
    
    message: hikari.Message = event.message
    me: hikari.OwnUser = plugin.bot.get_me()
    
    # If this message isn't a reply to us, or mentions us, then we aren't interested
    if (message.type == hikari.MessageType.REPLY and message.referenced_message.author.id != me.id) or \
       (me.id not in message.user_mentions_ids):
        return

    # Otherwise let's gather some context and reply to it
    cufoff = message.created_at - timedelta(seconds=CONFIG.openai.response_context_time)
    msgs = await plugin.bot.rest.fetch_messages(event.channel_id, after=cufoff)

    prompt = CONFIG.openai.response_prompt

    # Include the original message if it's not included
    if message.type == hikari.MessageType.REPLY and message.referenced_message is not None and \
       message.referenced_message not in msgs:
        prompt += f"\n{message.referenced_message.author.username}: {message.referenced_message}"

    for msg in msgs:
        # Give openai some context about who's replying to who
        username_part = f"{msg.author.username}"
        if msg.type == hikari.MessageType.REPLY and msg.referenced_message is not None:
            username_part += f" (in response to {msg.referenced_message.author})"
        prompt += f"\n{username_part}: {msg.content}"

    try:
        completion = await openai.Completion.acreate(
            model=CONFIG.openai.response_completions_model,
            max_tokens=CONFIG.openai.response_max_tokens,
            prompt=prompt
        )
        resp = completion.choices[0].text
        await plugin.bot.rest.create_message(event.channel_id, resp, reply=event.message_id)
    except openai.OpenAIError as e:
        logger.exception(f"Failed to automatically respond due to OpenAi Error: {e}")
        pass


@plugin.command
@lightbulb.add_cooldown(CONFIG.openai.command_cooldown, 1, lightbulb.UserBucket)
@lightbulb.option("prompt", "The Prompt to send to ChatGPT")
@lightbulb.command("askgpt", "Ask a question to OpenAI", pass_options=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def askgpt(ctx: lightbulb.context.SlashContext, prompt: str):
    embed = hikari.Embed(
        title=prompt,
        description="Please wait generating response",
        color=hikari.Colour(0x2ECC71)
    ).add_field('Requestor', f"<@{ctx.user.id}>")
    await ctx.respond(embed=embed)

    try:
        completion = await openai.Completion.acreate(
            model=CONFIG.openai.ask_completions_model,
            max_tokens=CONFIG.openai.ask_max_tokens,
            prompt=prompt
        )
    except openai.OpenAIError as e:
        await ctx.edit_last_response(
           embed=hikari.Embed(
                description=f"Failed to send request to ChatGPT: {e}",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return
    
    embed.description = completion.choices[0].text
    await ctx.edit_last_response(embed=embed)


@plugin.command
@lightbulb.add_cooldown(CONFIG.openai.command_cooldown, 1, lightbulb.UserBucket)
@lightbulb.option("size", "The size of the image to generate", default="1024x1024", choices=["256x256", "512x512", "1024x1024"])
@lightbulb.option("number", "Number of images to generate", default=4, type=int, required=False, max_value=CONFIG.openai.genimage_max_images)
@lightbulb.option("prompt", "The Prompt to send to ChatGPT")
@lightbulb.command("genimage", "Generates an image using OpenAI", pass_options=True)
@lightbulb.implements(lightbulb.commands.SlashCommand)
async def genimage(ctx: lightbulb.context.SlashContext, prompt: str, number: int, size: str):
    embed = hikari.Embed(
        title=prompt,
        description="Please wait generating response",
        color=hikari.Colour(0x2ECC71),
        url="https://openai.com"
    ).add_field('Requestor', f"<@{ctx.user.id}>")
    resp = await ctx.respond(embed=embed)

    try:
        images = await openai.Image.acreate(
            n=number,
            prompt=prompt,
            size=size
        )
    except openai.OpenAIError as e:
        await ctx.edit_last_response(
           embed=hikari.Embed(
                description=f"Failed to generate images: {e}",
                color=hikari.Colour(0xd32f2f)
            )
        )
        return

    image_data = []
    async with aiohttp.ClientSession() as session:
        for image in images.data:
            async with session.get(image['url']) as response:
                image_data.append(await response.read())

    await ctx.edit_last_response(embed=None, content="...")
    embed.description = None
   
    for image in image_data:
        msg = await resp.message()
        embed.set_image(image)
        embeds = msg.embeds + [embed]
        await msg.edit(embeds=embeds)
    await ctx.edit_last_response(content=None)


def load(bot: lightbulb.BotApp) -> None:
    if not CONFIG.openai or not CONFIG.openai.api_key:
        logger.warning('Not loading OpenAI plugin as openai.api_key is not defined in config')
        return

    bot.add_plugin(plugin)
    bot.d.openai: Dict[int, OpenAiContext] = defaultdict(lambda: OpenAiContext())


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
