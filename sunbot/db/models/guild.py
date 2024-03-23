import ormar
from sunbot.db.base import base_ormar_config


class Guild(ormar.Model):

    ormar_config = base_ormar_config.copy(
        tablename="guilds"
    )

    id: int = ormar.BigInteger(primary_key=True)
