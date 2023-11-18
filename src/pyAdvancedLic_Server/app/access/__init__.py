"""
Managing access and permissions
"""
from sqlalchemy.future import select
from sqlalchemy import func

from .. import config
from ..db import models, create_session
from .auth import get_password_hash
from .permissions import SUPERUSER


async def create_default_user_if_not_exists():
    """
    Creates a user with default username and password if no any users exist
    :return:
    """
    session = await anext(create_session())
    r = await session.execute(select(func.count()).select_from(models.User))
    if r.scalar() == 0:
        u = models.User(username=config.DEFAULT_USER,
                        hashed_password=get_password_hash(config.DEFAULT_PASSWORD),
                        permissions=SUPERUSER)
        session.add(u)
    await session.commit()
    await session.close()
