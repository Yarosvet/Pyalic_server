from sqlalchemy import create_engine
import sqlalchemy.orm as orm
import random
import string

from src.pyAdvancedLic_Server.app import config, db

conn_str = f'postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}'
engine = create_engine(conn_str, echo=False)
__factory = orm.sessionmaker(bind=engine, expire_on_commit=False)
from src.pyAdvancedLic_Server.app.db import models  # noqa


def rand_str(length: int) -> str:
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])


def rebuild_db():
    db.SqlAlchemyBase.metadata.drop_all(bind=engine)
    db.SqlAlchemyBase.metadata.create_all(bind=engine)
