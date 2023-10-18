from sqlalchemy.ext.asyncio import create_async_engine
import sqlalchemy.orm as orm
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy.ext.declarative as dec
from typing import AsyncIterator

SqlAlchemyBase = dec.declarative_base()

engine = None
__factory = None


async def global_init(user, password, hostname, db_name):
    """
    Globally init ASYNC PostgreSQL DB
    :param user: User of DB
    :param password: Password of DB
    :param hostname: Address of DB
    :param db_name: Name of DB
    """
    global __factory
    global engine
    if __factory:
        return
    conn_str = f'postgresql+asyncpg://{user}:{password}@{hostname}/{db_name}'
    engine = create_async_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    from . import models
    async with engine.begin() as conn:
        await conn.run_sync(SqlAlchemyBase.metadata.create_all)


async def create_session() -> AsyncIterator[AsyncSession]:
    global __factory
    async with __factory() as session:
        yield session
