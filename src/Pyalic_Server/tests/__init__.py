"""
Tests for FastAPI application
"""

import string
import random
from sqlalchemy import orm, text
from sqlalchemy.ext.serializer import dumps, loads
from sqlalchemy import create_engine

from ..app import config, db

conn_str = f'postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}'
ENGINE = create_engine(conn_str, echo=False)
__FACTORY = orm.sessionmaker(bind=ENGINE, expire_on_commit=False)

db_dump_tables = set()
db_dump_sequences = {}


def create_db_session() -> orm.Session:
    """
    Create sync SQLAlchemy Session
    """
    return __FACTORY()


def save_db_state():
    """
    Save database state to globals
    """
    with create_db_session() as session:
        for mapper in db.SqlAlchemyBase.registry.mappers:
            db_dump_tables.add(dumps(session.query(mapper.class_).all()))
        q = (i[0] for i in session.execute(text(
            "SELECT sequence_name FROM information_schema.sequences;"
        )).all())
        for seq_name in q:
            current_val = session.execute(text(f"SELECT nextval('{seq_name}')-1;")).scalar()
            if current_val != 0:
                db_dump_sequences[seq_name] = current_val


def load_db_state():
    """
    Load database from saved state
    """
    with create_db_session() as session:
        for table_class in db_dump_tables:
            restored = loads(table_class, scoped_session=orm.scoped_session(__FACTORY))
            for obj in restored:
                session.merge(obj)
            session.commit()
        q = (i[0] for i in session.execute(text(
            "SELECT sequence_name FROM information_schema.sequences;"
        )).all())
        for seq_name in q:
            if seq_name in db_dump_sequences:
                current_value = db_dump_sequences[seq_name]
                session.execute(text(f"SELECT setval('{seq_name}', {current_value});"))


def clean_db():
    """
    Drop all models in database
    """
    db.SqlAlchemyBase.metadata.drop_all(bind=ENGINE)


def fill_db():
    """
    Create all models in database
    """
    db.SqlAlchemyBase.metadata.create_all(bind=ENGINE)


def rand_str(length: int) -> str:
    """
    Generate random string of letters and digits
    :param length: Required length of string
    :return:
    """
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])
