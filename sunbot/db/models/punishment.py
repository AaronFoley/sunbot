import ormar
from sunbot.db.base import base_ormar_config
from sunbot.db.models.guild import Guild


class PunishmentConfig(ormar.Model):

    ormar_config = base_ormar_config.copy(
        tablename="punishment_config"
    )

    id: int = ormar.Integer(primary_key=True, autoincrement=True)
    guild: Guild = ormar.ForeignKey(Guild, related_name="punishment", unique=True)
    channel: int = ormar.BigInteger(nullable=True, default=None)


class PunishmentSong(ormar.Model):

    ormar_config = base_ormar_config.copy(
        tablename="punishment_songs",
        constraints=[ormar.UniqueColumns("name", "guild")]
    )

    id: int = ormar.Integer(primary_key=True, autoincrement=True)
    guild: Guild = ormar.ForeignKey(Guild, related_name="punishment_songs")
    name: str = ormar.String(max_length=255)
    url: str = ormar.String(max_length=255)
