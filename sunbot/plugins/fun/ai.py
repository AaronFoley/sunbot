import logging
import random
import time
from datetime import timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Sequence
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
client = openai.AsyncOpenAI(api_key=CONFIG.openai.api_key)


@dataclass
class OpenAiRandomContext:
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


def generate_messages(msgs: Sequence[Message]) -> List[Dict]:
    """ Given a sequence of messages, generate the chat messgaes to send to OpenAI """

    me: hikari.OwnUser = plugin.bot.get_me()
    chat_messages = []

    # Incldue the context messages from the config
    for msg in CONFIG.openai.auto.system_context:
        chat_messages.append({
            "role": "system",
            "content": msg,
        })

    for msg in msgs:
        role = 'assistant' if msg.author.id == me.id else 'user'
        content = msg.content

        if role == 'user':
            content = f'{msg.author.username}: {content}'

        # If we are using a vision, we need to workout if there are any images included
        if CONFIG.openai.auto.use_vision:
            content = [
                 {"type": "text", "text": content},
            ]

            for attach in msg.attachments:
                if not attach.media_type.lower().startswith('image'):
                    continue

                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": attach.url,
                    }
                })

        chat_messages.append({
            "role": role,
            "content": content
        })

    return chat_messages


@tasks.task(s=10, auto_start=True)
async def auto_repsonse():
    """ Do the auto response """

    all_context: Dict[int, OpenAiRandomContext] = plugin.bot.d.openai

    now = time.time()

    for _, octx in all_context.items():
        if octx.target_message is None:
            return

        # If we are below both the timeout and last poll phase then wait some more
        if now < (octx.last_trigger + CONFIG.openai.auto.context_timeout):
            if now < (octx.last_context + CONFIG.openai.auto.context_poll):
                return

        logger.info(f'Generating reponse to {octx.target_message.id}')

        chat_messages = generate_messages(octx.messages)

        try:
            response = await client.chat.completions.create(
                model=CONFIG.openai.auto.completions_model,
                max_tokens=CONFIG.openai.auto.random.max_tokens,
                messages=chat_messages
            )
            await plugin.bot.rest.create_message(octx.target_message.channel_id, response.choices[0].message.content)
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

    octx: OpenAiRandomContext = plugin.bot.d.openai[event.guild_id]
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

    # If this is a reply to an earlier message, than use the original message
    if (message.type == hikari.MessageType.REPLY):
        message = message.referenced_message

    # Otherwise let's gather some context and reply to it
    cufoff = message.created_at - timedelta(seconds=CONFIG.openai.auto.reply.pre_context_time)
    msgs = plugin.bot.rest.fetch_messages(event.channel_id, after=cufoff).limit(
        CONFIG.openai.auto.reply.pre_context_limit
    )

    chat_messages = generate_messages(await msgs)

    try:
        response = await client.chat.completions.create(
            model=CONFIG.openai.auto.completions_model,
            max_tokens=CONFIG.openai.auto.reply.max_tokens,
            messages=chat_messages
        )
        await plugin.bot.rest.create_message(event.channel_id, response.choices[0].message.content, reply=event.message_id)
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
    bot.d.openai: Dict[int, OpenAiRandomContext] = defaultdict(lambda: OpenAiRandomContext())


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
