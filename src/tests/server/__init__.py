from sqlalchemy import create_engine
import random
import string
from sqlalchemy import orm
from sqlalchemy.ext.serializer import dumps, loads

from src.pyAdvancedLic_Server.app import config, db

conn_str = f'postgresql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}'
engine = create_engine(conn_str, echo=False)
__factory = orm.sessionmaker(bind=engine, expire_on_commit=False)

db_dump_tables = set()
db_dump_sequences = {}


def create_db_session() -> orm.Session:
    return __factory()


def save_db_state():
    global db_dump_tables
    global db_dump_sequences
    with create_db_session() as session:
        for mapper in db.SqlAlchemyBase.registry.mappers:
            db_dump_tables.add(dumps(session.query(mapper.class_).all()))
        q = (i[0] for i in session.execute("SELECT sequence_name FROM information_schema.sequences;").all())
        for seq_name in q:
            current_val = session.execute(f"SELECT nextval('{seq_name}')-1;").scalar()
            if current_val != 0:
                db_dump_sequences[seq_name] = current_val


def load_db_state():
    with create_db_session() as session:
        for table_class in db_dump_tables:
            restored = loads(table_class, scoped_session=orm.scoped_session(__factory))
            for obj in restored:
                session.merge(obj)
            session.commit()
        q = (i[0] for i in session.execute("SELECT sequence_name FROM information_schema.sequences;").all())
        for seq_name in q:
            if seq_name in db_dump_sequences.keys():
                current_value = db_dump_sequences[seq_name]
                session.execute(f"SELECT setval('{seq_name}', {current_value});")


def clean_db():
    db.SqlAlchemyBase.metadata.drop_all(bind=engine)


def fill_db():
    db.SqlAlchemyBase.metadata.create_all(bind=engine)


def rand_str(length: int) -> str:
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])
