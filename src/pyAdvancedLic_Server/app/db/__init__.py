"""
Actions with Database
"""
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

ENGINE = None
__FACTORY = None


async def global_init(user, password, hostname, db_name):
    """
    Globally init ASYNC PostgreSQL DB
    :param user: User of DB
    :param password: Password of DB
    :param hostname: Address of DB
    :param db_name: Name of DB
    """
    global __FACTORY  # pylint: disable=W0603
    global ENGINE  # pylint: disable=W0603
    if __FACTORY:
        return
    conn_str = f'postgresql+asyncpg://{user}:{password}@{hostname}/{db_name}'
    ENGINE = create_async_engine(conn_str, echo=False)
    __FACTORY = sessionmaker(bind=ENGINE, class_=AsyncSession, expire_on_commit=False)
    async with ENGINE.begin() as conn:
        await conn.run_sync(SqlAlchemyBase.metadata.create_all)


async def create_session() -> AsyncIterator[AsyncSession]:
    """Create async session to configured database"""
    async with __FACTORY() as session:
        yield session
