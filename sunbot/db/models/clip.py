from typing import Optional
import ormar
from sunbot.db.base import BaseMeta
from sunbot.db.models.guild import Guild


class Clip(ormar.Model):

    class Meta(BaseMeta):
        tablename = "clips"
        constraints = [ormar.UniqueColumns("name", "guild")]

    id: int = ormar.Integer(primary_key=True, autoincrement=True,)
    guild: Guild = ormar.ForeignKey(Guild, related_name="clips")
    author: str = ormar.BigInteger()
    name: str = ormar.String(max_length=50)
    url: str = ormar.String(max_length=255)
    seek: Optional[int] = ormar.Integer(nullable=True)
