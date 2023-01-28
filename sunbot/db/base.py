import sqlalchemy as sa
from ormar import ModelMeta
from databases import Database
from sunbot.config import CONFIG


meta = sa.MetaData()
database = Database(CONFIG.database.url)


class BaseMeta(ModelMeta):
    """Base metadata for models."""

    database = database
    metadata = meta
