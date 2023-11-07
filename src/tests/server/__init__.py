from sqlalchemy import create_engine
import random
import string
from sqlalchemy import orm
from sqlalchemy.ext.serializer import dumps, loads

from src.pyAdvancedLic_Server.app import config, db

conn_str = f'postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}'
engine = create_engine(conn_str, echo=False)
__factory = orm.sessionmaker(bind=engine, expire_on_commit=False)
db.SqlAlchemyBase.metadata.drop_all(bind=engine)

db_dump = None


def save_db_state():
    global db_dump
    with __factory() as session:
        db_dump = dumps(session)


def load_db_state():
    loads(db_dump, scoped_session=orm.scoped_session(__factory))


def rand_str(length: int) -> str:
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])
