"""
Test all about checking license key and interaction with sessions
"""
import time
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from ..app import config
from ..app.db import models

from . import rand_str, create_db_session


# pylint: disable=C0116

@pytest.mark.usefixtures('client', 'rebuild_db')
class TestKeySession:  # pylint: disable=C0115
    @staticmethod
    def __create_rand_product(inst_lim: int = None,
                              sessions_lim: int = None,
                              sig_period: timedelta = None) -> int:
        with create_db_session() as session:
            p = models.Product(name=rand_str(16),
                               sig_install_limit=inst_lim,
                               sig_sessions_limit=sessions_lim,
                               sig_period=sig_period)
            session.add(p)
            session.commit()
            session.refresh(p)
            return p.id

    def __create_rand_signature(self, product_id: int = None) -> tuple[int, str]:
        if product_id is None:
            product_id = self.__create_rand_product()
        key = rand_str(32)
        with create_db_session() as session:
            s = models.Signature(product_id=product_id, license_key=key)
            session.add(s)
            session.commit()
            session.refresh(s)
            return s.id, key

    def __create_rand_session(self, client: TestClient, license_key: str = None) -> str:
        if license_key is None:
            license_key = self.__create_rand_signature()[1]
        p = {
            "license_key": license_key,
            "fingerprint": rand_str(16)
        }
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 200
        return r.json()['session_id']

    def test_wrong_key(self, client):
        p = {
            "license_key": rand_str(16),
            "fingerprint": rand_str(16)
        }
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 403
        assert not r.json()['success'] and 'error' in r.json().keys()

    def test_valid_key(self, client):
        key = self.__create_rand_signature()[1]
        p = {
            "license_key": key,
            "fingerprint": rand_str(16)
        }
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 200
        assert r.json()['success'] and r.json()['session_id']

    def test_immediately_end_session(self, client):
        """Create session by verifying key and immediately end it"""
        session_id = self.__create_rand_session(client)
        p = {
            "session_id": session_id
        }
        r = client.request('POST', '/end_session', json=p)
        assert r.status_code == 200
        assert r.json()['success']

    def test_keepalive_end_session(self, client):
        """Create session, send some keepalive packets, then end it"""
        session_id = self.__create_rand_session(client)
        p = {
            "session_id": session_id
        }
        for _ in range(2):
            time.sleep(1)
            r = client.request('POST', '/keepalive', json=p)
            assert r.status_code == 200
        time.sleep(1)
        r = client.request('POST', '/end_session', json=p)
        assert r.status_code == 200
        assert r.json()['success']

    def test_auto_end_session(self, client):
        """Create session and wait until it gets expired"""
        session_id = self.__create_rand_session(client)
        p = {
            "session_id": session_id
        }
        time.sleep(config.SESSION_ALIVE_PERIOD + 2.1)
        r = client.request('POST', '/keepalive', json=p)
        assert r.status_code == 404

    def test_keepalive_auto_end_session(self, client):
        """Create session, send some keepalive packets and wait until it gets expired"""
        session_id = self.__create_rand_session(client)
        p = {
            "session_id": session_id
        }
        for _ in range(2):
            time.sleep(1)
            r = client.request('POST', '/keepalive', json=p)
            assert r.status_code == 200
        time.sleep(config.SESSION_ALIVE_PERIOD + 2.1)
        r = client.request('POST', '/keepalive', json=p)
        assert r.status_code == 404

    def test_limit_installs(self, client):
        """Test abusing installations limit"""
        product_id = self.__create_rand_product(inst_lim=1)
        key = self.__create_rand_signature(product_id)[1]
        p = {
            "license_key": key,
            "fingerprint": rand_str(16)
        }
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 200
        client.request('POST', '/end_session', json={"session_id": r.json()["session_id"]})
        p['fingerprint'] = rand_str(16)
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 403
        assert r.json() == {'error': 'Installations limit exceeded', 'success': False}

    def test_limit_sessions(self, client):
        """Test abusing sessions limit"""
        product_id = self.__create_rand_product(sessions_lim=1)
        key = self.__create_rand_signature(product_id)[1]
        p = {
            "license_key": key,
            "fingerprint": rand_str(16)
        }
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 200
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 403
        assert r.json() == {'error': 'Sessions limit exceeded', 'success': False}

    def test_signature_exp_after_activation(self, client):
        """Test the case when signature expires when session ended"""
        sig_period = 5
        product_id = self.__create_rand_product(sig_period=timedelta(seconds=sig_period))
        key = self.__create_rand_signature(product_id)[1]
        p = {
            "license_key": key,
            "fingerprint": rand_str(16)
        }
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 200
        r = client.request('POST', '/end_session', json={"session_id": r.json()["session_id"]})
        assert r.status_code == 200
        time.sleep(sig_period)
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 403
        assert r.json() == {'error': 'License expired', 'success': False}

    def test_signature_exp_while_session(self, client):
        """Test the case when signature expires while session is active"""
        sig_period = 1
        product_id = self.__create_rand_product(sig_period=timedelta(seconds=sig_period))
        key = self.__create_rand_signature(product_id)[1]
        p = {
            "license_key": key,
            "fingerprint": rand_str(16)
        }
        r = client.request('GET', '/check_license', json=p)
        assert r.status_code == 200
        time.sleep(sig_period + 2)
        r = client.request('POST', '/keepalive', json={"session_id": r.json()['session_id']})
        assert r.status_code == 404
