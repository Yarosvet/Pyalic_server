"""
Sessions mechanics
"""
import random
from string import ascii_letters, digits
from datetime import datetime

from . import redis
from .. import config
from ..loggers import logger


class SessionNotFoundException(Exception):
    """
    Requested Session ID not found
    """


def _random_session_id(signature_id: int, signature_ends: int) -> str:
    return f"{str(signature_id)}:{signature_ends}:" + "".join(
        [random.choice(ascii_letters + digits) for _ in range(32)])


async def create_session(signature_id: int, signature_ends: int) -> str:
    """
    Create licensing session
    :param signature_id: ID of Signature
    :param signature_ends: Timestamp when session must be ended because of signature expiration
    :return: Session ID
    """
    session_id = _random_session_id(signature_id, signature_ends)
    while await redis.exists(session_id):
        # While current ID already exists, create different one
        session_id = _random_session_id(signature_id, signature_ends)
    # Add session to redis
    if signature_ends - config.SESSION_ALIVE_PERIOD > datetime.now().timestamp():
        # Signature doesn't expire end before session should expire
        await redis.set(session_id, 1, ex=config.SESSION_ALIVE_PERIOD)
    else:
        # Signature must be expired with session
        await redis.set(session_id, 1, exat=signature_ends)
    await logger.info(f"Created new session {session_id}")
    return session_id


async def keep_alive(session_id: str):
    """
    Keep-alive session
    :param session_id: Session ID
    """
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    signature_ends = int(session_id.split(":")[1])
    if signature_ends - config.SESSION_ALIVE_PERIOD > datetime.now().timestamp():
        # Signature doesn't expire end before session should expire
        await redis.set(session_id, 1, ex=config.SESSION_ALIVE_PERIOD)
    else:
        # Signature must be expired with session
        await redis.set(session_id, 1, exat=signature_ends)


async def end_session(session_id: str):
    """
    Correctly end session
    :param session_id: Session ID
    """
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    await redis.delete(session_id)  # Just delete session from redis
    await logger.info(f"Ended session {session_id}")


async def search_sessions(signature_id: int) -> list[str]:
    """
    Get active session IDs of specified signature
    :param signature_id: Signature ID
    :return:
    """
    res = []
    async for session_id in redis.scan_iter(match=f"{signature_id}:*:*"):
        res.append(session_id)
    return res
