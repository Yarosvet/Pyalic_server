"""
Licensing and sessions mechanics placed here
"""
from redis.asyncio import Redis

from .. import config

redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, password=config.REDIS_PASSWORD)
