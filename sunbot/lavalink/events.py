import logging
import lavalink

logger = logging.getLogger(__name__)


class EventHandler:
    """Events from the Lavalink server"""

    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):
        logger.info('Track started on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.TrackEndEvent)
    async def track_end(self, event: lavalink.TrackEndEvent):
        logger.info('Track finished on guild: %s', event.player.guild_id)

    @lavalink.listener(lavalink.TrackExceptionEvent)
    async def track_exception(self, event: lavalink.TrackExceptionEvent):
        logger.warning('Track exception event happened on guild: %d', event.player.guild_id)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        logger.info('Queue finished on guild: %s', event.player.guild_id)
