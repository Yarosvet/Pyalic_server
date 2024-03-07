"""
Here we got pytest fixtures set up
"""
import time
import pytest
from fastapi.testclient import TestClient
from redis import StrictRedis

from ..app import config, app

from . import load_db_state, save_db_state, clean_db, fill_db


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Get FastAPI TestClient
    """
    with TestClient(app) as c:
        time.sleep(1)
        save_db_state()
        yield c


@pytest.fixture(scope="function")
def rebuild_db(redis_client: StrictRedis):  # pylint: disable=W0621
    """
    Rebuild db with saved state
    """
    redis_client.flushall()
    clean_db()
    fill_db()
    load_db_state()


@pytest.fixture(scope="session")
def redis_client():
    """
    Safely get sync Redis client
    """
    with StrictRedis(config.REDIS_HOST, config.REDIS_PORT, config.REDIS_DB, config.REDIS_PASSWORD) as r:
        yield r


@pytest.fixture(scope="session", autouse=True)
def clean_db_on_start_and_finish(redis_client):  # pylint: disable=W0621
    """
    Rebuild db before test passed and after
    """
    clean_db()
    yield
    clean_db()
    redis_client.flushall()


@pytest.fixture(scope="class")
def auth(client) -> dict[str, str]:  # pylint: disable=W0621
    """
    Get authentication of default user
    """
    p = {
        "grant_type": "password",
        "username": config.DEFAULT_USER,
        "password": config.DEFAULT_PASSWORD
    }
    r = client.request('POST', '/admin/token', data=p)
    token = r.json()['access_token']
    yield {'Authorization': f"Bearer {token}"}
