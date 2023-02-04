import ormar
from sunbot.db.base import BaseMeta
from sunbot.db.models.guild import Guild


class PunishmentConfig(ormar.Model):

    class Meta(BaseMeta):
        tablename = "punishment_config"

    id: int = ormar.Integer(primary_key=True, autoincrement=True)
    guild: Guild = ormar.ForeignKey(Guild, related_name="punishment", unique=True)
    channel: int = ormar.BigInteger(nullable=True, default=None)


class PunishmentSong(ormar.Model):

    class Meta(BaseMeta):
        tablename = "punishment_songs"
        constraints = [ormar.UniqueColumns("name", "guild")]

    id: int = ormar.Integer(primary_key=True, autoincrement=True)
    guild: Guild = ormar.ForeignKey(Guild, related_name="punishment_songs")
    name: str = ormar.String(max_length=255)
    url: str = ormar.String(max_length=255)
