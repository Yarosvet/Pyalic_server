import random
from string import ascii_letters, digits
from datetime import datetime

from . import redis
from .. import config
from ..loggers import logger


class SessionNotFoundException(Exception):
    pass


def _random_session_id(signature_id: int, signature_ends: int):
    return f"{str(signature_id)}:{signature_ends}:" + "".join(
        [random.choice(ascii_letters + digits) for _ in range(32)])


async def create_session(signature_id: int, signature_ends: int) -> str:
    session_id = _random_session_id(signature_id, signature_ends)
    while await redis.exists(session_id):
        session_id = _random_session_id(signature_id, signature_ends)
    await redis.set(session_id, datetime.utcnow().isoformat())
    await logger.info(f"Created new session {session_id}")
    return session_id


async def keep_alive(session_id: str):
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    await redis.set(session_id, datetime.utcnow().isoformat())


async def end_session(session_id: str):
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    await redis.delete(session_id)
    await logger.info(f"Ended session {session_id}")


async def search_sessions(signature_id: int) -> list[str]:
    res = []
    async for session_id in redis.scan_iter(match=f"{signature_id}:*:*"):
        res.append(session_id)
    return res


async def clean_expired_sessions():
    async for session_id in redis.scan_iter(match="*:*:*"):
        last_keepalive_str = await redis.get(session_id)
        delta_alive = (datetime.utcnow() - datetime.fromisoformat(last_keepalive_str.decode('utf-8'))).total_seconds()
        sig_ends_timestamp = int(session_id.decode('utf-8').split(":")[1])
        if delta_alive >= config.SESSION_ALIVE_PERIOD:
            await redis.delete(session_id)
            await logger.info(f"Session {session_id} cleaned because of inactivity")
        if sig_ends_timestamp != 0 and datetime.fromtimestamp(sig_ends_timestamp) < datetime.utcnow():
            await redis.delete(session_id)
            await logger.info(f"Session {session_id} cleaned because the signature expired")
