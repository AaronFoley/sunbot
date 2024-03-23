import sqlalchemy
import ormar
from databases import Database
from sunbot.config import CONFIG

database = Database(CONFIG.database.url)

base_ormar_config = ormar.OrmarConfig(
    database=database,
    metadata=sqlalchemy.MetaData()
)
