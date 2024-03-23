from __future__ import annotations
import typing as t

from sunbot.bot import Sunbot

import hikari
from hikari.api import VoiceConnection, VoiceComponent
import lavalink


class LavalinkVoice(VoiceConnection):
    __slots__ = [
        "lavalink",
        "player",
        "__channel_id",
        "__guild_id",
        "__session_id",
        "__is_alive",
        "__shard_id",
        "__on_close",
        "__owner",
    ]
    lavalink: lavalink.Client
    player: lavalink.DefaultPlayer

    def __init__(
        self,
        lavalink_client: lavalink.Client,
        player: lavalink.DefaultPlayer,
        *,
        channel_id: hikari.Snowflake,
        guild_id: hikari.Snowflake,
        session_id: str,
        is_alive: bool,
        shard_id: int,
        owner: VoiceComponent,
        on_close: t.Any,
    ) -> None:
        self.player = player
        self.lavalink = lavalink_client

        self.__channel_id = channel_id
        self.__guild_id = guild_id
        self.__session_id = session_id
        self.__is_alive = is_alive
        self.__shard_id = shard_id
        self.__owner = owner
        self.__on_close = on_close

    @property
    def channel_id(self) -> hikari.Snowflake:
        """Return the ID of the voice channel this voice connection is in."""
        return self.__channel_id

    @property
    def guild_id(self) -> hikari.Snowflake:
        """Return the ID of the guild this voice connection is in."""
        return self.__guild_id

    @property
    def is_alive(self) -> bool:
        """Return `builtins.True` if the connection is alive."""
        return self.__is_alive

    @property
    def shard_id(self) -> int:
        """Return the ID of the shard that requested the connection."""
        return self.__shard_id

    @property
    def owner(self) -> VoiceComponent:
        """Return the component that is managing this connection."""
        return self.__owner

    async def disconnect(self) -> None:
        """Signal the process to shut down."""
        self.__is_alive = False

        self.player.queue.clear()
        await self.player.stop()
        await self.__on_close(self)

    async def join(self) -> None:
        """Wait for the process to halt before continuing."""

    async def notify(self, event: hikari.VoiceEvent) -> None:
        """Submit an event to the voice connection to be processed."""
        if isinstance(event, hikari.VoiceServerUpdateEvent):
            await self.player._voice_server_update({
                'endpoint': event.endpoint[6:],  # get rid of wss://
                'token': event.token,
            })

    @classmethod
    async def connect(
        cls,
        guild_id: hikari.Snowflake,
        channel_id: hikari.Snowflake,
        client: Sunbot,
        lavalink_client: lavalink.Client,
        player_data: t.Any,
        deaf: bool = True,
    ) -> LavalinkVoice:
        voice: LavalinkVoice = await client.voice.connect_to(
            guild_id,
            channel_id,
            voice_connection_type=LavalinkVoice,
            lavalink_client=lavalink_client,
            player_data=player_data,
            deaf=deaf,
        )
        return voice

    @classmethod
    async def initialize(
        cls,
        channel_id: hikari.Snowflake,
        endpoint: str,
        guild_id: hikari.Snowflake,
        on_close: t.Any,
        owner: VoiceComponent,
        session_id: str,
        shard_id: int,
        token: str,
        user_id: hikari.Snowflake,
        **kwargs: t.Any,
    ) -> LavalinkVoice:
        lavalink_client: lavalink.Client = kwargs["lavalink_client"]
        player = lavalink_client.player_manager.create(guild_id)

        await player._voice_state_update({
            'user_id': user_id,
            'channel_id': channel_id,
            'session_id': session_id,
            'endpoint': endpoint[6:],  # get rid of wss://
            'token': token,
        })

        await player._voice_server_update({
            'user_id': user_id,
            'channel_id': channel_id,
            'session_id': session_id,
            'endpoint': endpoint[6:],  # get rid of wss://
            'token': token,
        })

        self = LavalinkVoice(
            lavalink_client,
            player,
            channel_id=channel_id,
            guild_id=guild_id,
            session_id=session_id,
            is_alive=True,
            shard_id=shard_id,
            owner=owner,
            on_close=on_close,
        )

        return self
