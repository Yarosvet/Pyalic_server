import random
from string import ascii_letters, digits
from datetime import datetime

from . import redis


class SessionNotFoundException(Exception):
    pass


def _random_session_id(signature_id: int):
    return f"{str(signature_id)}:" + "".join([random.choice(ascii_letters + digits) for _ in range(32)])


async def create_session(signature_id: int) -> str:
    session_id = _random_session_id(signature_id)
    while await redis.exists(session_id):
        session_id = _random_session_id(signature_id)
    await redis.set(session_id, datetime.utcnow().isoformat())
    return session_id


async def keep_alive(session_id: str):
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    await redis.set(session_id, datetime.utcnow().isoformat())


async def end_session(session_id: str):
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    await redis.delete(session_id)


async def search_sessions(signature_id: int) -> list[str]:
    res = []
    async for session_id in redis.scan_iter(match=f"{signature_id}:*"):
        res.append(session_id)
    return res
