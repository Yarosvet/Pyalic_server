import pytest
from fastapi.testclient import TestClient
import time

from src.pyAdvancedLic_Server.app import config, app

from . import load_db_state, save_db_state, clean_db


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        time.sleep(1)
        save_db_state()
        yield c


@pytest.fixture(scope="function")
def rebuild_db():
    load_db_state()


@pytest.fixture(scope="session", autouse=True)
def clean_db_on_finish():
    yield
    clean_db()


@pytest.fixture(scope="class")
def auth(client):
    p = {
        "grant_type": "password",
        "username": config.DEFAULT_USER,
        "password": config.DEFAULT_PASSWORD
    }
    r = client.request('POST', '/admin/token', data=p)
    token = r.json()['access_token']
    yield {'Authorization': f"Bearer {token}"}
