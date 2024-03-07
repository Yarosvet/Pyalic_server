"""
Actions with Database
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import NullPool

SqlAlchemyBase = declarative_base()

ENGINE = None
__FACTORY = None


async def global_init(user: str, password: str, hostname: str, db_name: str):
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
    ENGINE = create_async_engine(conn_str, echo=False, poolclass=NullPool)
    __FACTORY = sessionmaker(bind=ENGINE, class_=AsyncSession, expire_on_commit=False)
    async with ENGINE.begin() as conn:
        # Create all models
        await conn.run_sync(SqlAlchemyBase.metadata.create_all)


async def session_dep() -> AsyncIterator[AsyncSession]:
    """Create async session to configured database"""
    async with __FACTORY() as session:  # noqa
        yield session


@asynccontextmanager
async def create_session() -> AsyncSession:
    """Create async session to configured database"""
    try:
        async with __FACTORY() as session:  # noqa
            yield session
    finally:
        await session.close()
