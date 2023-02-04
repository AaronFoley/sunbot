import ormar
from sunbot.db.base import BaseMeta


class Guild(ormar.Model):

    class Meta(BaseMeta):
        tablename = "guilds"

    id: int = ormar.BigInteger(primary_key=True)
