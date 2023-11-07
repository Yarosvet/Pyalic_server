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


def create_db_session() -> orm.Session:
    return __factory()


def save_db_state():
    global db_dump
    with create_db_session() as session:
        db_dump = dumps(session)


def load_db_state():
    loads(db_dump, scoped_session=orm.scoped_session(__factory))


def clean_db():
    db.SqlAlchemyBase.metadata.drop_all(bind=engine)


def rand_str(length: int) -> str:
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])


def create_rand_user(permissions: str, master_username: str = None) -> tuple[int, str, str]:
    """
    :param master_username: Master's username
    :param permissions: User's permissions string
    :return: username and password
    """

