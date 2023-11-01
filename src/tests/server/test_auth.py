from fastapi.testclient import TestClient

from src.pyAdvancedLic_Server.app import app, config

from . import rebuild_db, rand_str


class TestGettingToken:
    client: TestClient = None

    @classmethod
    def setup_class(cls):
        rebuild_db()
        cls.client = TestClient(app).__enter__()

    @classmethod
    def teardown_class(cls):
        cls.client.__exit__()

    def test_wrong_access_token(self):
        h = {'Authorization': f'Bearer {rand_str(16)}'}
        r = self.client.get('/admin/users/me', headers=h)
        assert r.status_code == 401
        assert 'id' not in r.json().keys() and 'username' not in r.json().keys()

    def test_getting_me(self):
        p = {
            "grant_type": "password",
            "username": config.DEFAULT_USER,
            "password": config.DEFAULT_PASSWORD
        }
        r = self.client.post('/admin/token', data=p)
        assert r.status_code == 200
        assert 'access_token' in r.json().keys() and r.json()['access_token']
        assert 'token_type' in r.json().keys() and r.json()['token_type'] == "bearer"
        token = r.json()['access_token']
        h = {'Authorization': f'Bearer {token}'}
        r = self.client.get('/admin/users/me', headers=h)
        d = r.json()
        assert 'id' in d.keys() and 'username' in d.keys()

    def test_wrong_password(self):
        p = {
            "grant_type": "password",
            "username": config.DEFAULT_USER,
            "password": rand_str(16)
        }
        r = self.client.post('/admin/token', data=p)
        assert r.status_code == 401
        assert 'access_token' not in r.json().keys()
        assert 'token_type' not in r.json().keys()

    def test_wrong_user(self):
        p = {
            "grant_type": "password",
            "username": rand_str(16),
            "password": config.DEFAULT_PASSWORD
        }
        r = self.client.post('/admin/token', data=p)
        assert r.status_code == 401
        assert 'access_token' not in r.json().keys()
        assert 'token_type' not in r.json().keys()
