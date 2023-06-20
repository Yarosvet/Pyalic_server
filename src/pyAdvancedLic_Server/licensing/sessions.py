import random
from string import ascii_letters, digits
from datetime import datetime

from . import redis


class SessionNotFoundException(Exception):
    pass


def _random_string(length: int):
    return "".join([random.choice(ascii_letters + digits) for _ in range(length)])


async def create_session(signature_id: int) -> str:
    session_id = _random_string(32)
    while await redis.exists(session_id):
        session_id = _random_string(32)
    session = {'signature_id': signature_id, 'last_keepalive': datetime.utcnow().isoformat()}
    await redis.hmset(session_id, session)
    return session_id


async def keep_alive(session_id: str):
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    await redis.hset(session_id, key='last_keepalive', value=datetime.utcnow().timestamp())


async def end_session(session_id: str):
    if not await redis.exists(session_id):
        raise SessionNotFoundException
    await redis.delete(session_id)
