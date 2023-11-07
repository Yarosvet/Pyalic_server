import pytest

from src.pyAdvancedLic_Server.app import config
from src.pyAdvancedLic_Server.app.db import models
from src.pyAdvancedLic_Server.app.access.auth import check_password
from src.pyAdvancedLic_Server.app.access.auth import get_password_hash

from . import rand_str, create_db_session


@pytest.mark.usefixtures('client', 'rebuild_db')
class TestAuth:
    def test_wrong_access_token(self, client):
        h = {'Authorization': f'Bearer {rand_str(16)}'}
        r = client.request('GET', '/admin/users/me', headers=h)
        assert r.status_code == 401
        assert 'id' not in r.json().keys() and 'username' not in r.json().keys()

    def test_valid_creds(self, client):
        p = {
            "grant_type": "password",
            "username": config.DEFAULT_USER,
            "password": config.DEFAULT_PASSWORD
        }
        r = client.request('POST', '/admin/token', data=p)
        assert r.status_code == 200
        assert 'access_token' in r.json().keys() and r.json()['access_token']
        assert 'token_type' in r.json().keys() and r.json()['token_type'] == "bearer"

    def test_wrong_password(self, client):
        p = {
            "grant_type": "password",
            "username": config.DEFAULT_USER,
            "password": rand_str(16)
        }
        r = client.request('POST', '/admin/token', data=p)
        assert r.status_code == 401
        assert 'access_token' not in r.json().keys()
        assert 'token_type' not in r.json().keys()

    def test_wrong_user(self, client):
        p = {
            "grant_type": "password",
            "username": rand_str(16),
            "password": config.DEFAULT_PASSWORD
        }
        r = client.request('POST', '/admin/token', data=p)
        assert r.status_code == 401
        assert 'access_token' not in r.json().keys()
        assert 'token_type' not in r.json().keys()


@pytest.mark.usefixtures('client', 'rebuild_db', 'auth')
class TestUsersOperations:
    def test_list_users(self, client, auth):
        p = {
            'limit': 100,
            'offset': 0
        }
        r = client.request('GET', '/admin/users/list', json=p, headers=auth)
        assert r.status_code == 200
        assert r.json() == {'items': 1, 'users': [{'id': 1, 'username': 'user'}]}

    def test_getting_me(self, client, auth):
        r = client.request('GET', '/admin/users/me', headers=auth)
        j = r.json()
        assert 'id' in j.keys() and 'username' in j.keys() and j['username'] == config.DEFAULT_USER

    def test_add_user(self, client, auth):
        username = rand_str(16)
        password = rand_str(16)
        permissions = "superuser"
        p = {
            "username": username,
            "password": password,
            "permissions": permissions
        }
        r = client.request('POST', '/admin/users/interact_user', json=p, headers=auth)
        j = r.json()
        assert r.status_code == 200
        assert 'id' in j.keys() and 'master_id' in j.keys() and 'username' in j.keys()
        with create_db_session() as session:
            me = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none()
            u = session.query(models.User).filter_by(id=j['id']).one_or_none()
            assert u in me.slaves
            assert u.permissions == j['permissions'] == permissions
            assert u.username == j['username'] == username
            assert check_password(password, u.hashed_password)

    def test_get_user(self, client, auth):
        permissions = "superuser"
        username = rand_str(16)
        password = rand_str(16)
        with create_db_session() as session:
            master_id = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none().id
            u = models.User(username=username,
                            hashed_password=get_password_hash(password),
                            permissions=permissions,
                            master_id=master_id)
            session.add(u)
            session.commit()
            session.refresh(u)
            p = {'id': u.id}
            r = client.request('GET', '/admin/users/interact_user', json=p, headers=auth)
            assert r.status_code == 200
            j = r.json()
            assert j['username'] == username
            assert j['id'] == u.id
            assert j['permissions'] == permissions
            assert j['master_id'] == u.master_id

    def test_update_user(self, client, auth):
        permissions = "superuser"
        username = rand_str(16)
        password = rand_str(16)
        new_permissions = "manage_own_products"
        new_username = rand_str(16)
        new_password = rand_str(16)
        with create_db_session() as session:
            master_id = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none().id
            u = models.User(username=username,
                            hashed_password=get_password_hash(password),
                            permissions=permissions,
                            master_id=master_id)
            session.add(u)
            session.commit()
            p = {
                'id': u.id,
                'username': new_username,
                'password': new_password,
                'permissions': new_permissions
            }
            r = client.request('PUT', '/admin/users/interact_user', json=p, headers=auth)
            assert r.status_code == 200
            session.refresh(u)
            j = r.json()
            assert j['username'] == new_username
            assert j['id'] == u.id
            assert j['permissions'] == new_permissions == u.permissions
            assert j['master_id'] == u.master_id
            assert check_password(new_password, u.hashed_password)

    def test_delete_user(self, client, auth):
        permissions = "superuser"
        username = rand_str(16)
        password = rand_str(16)
        with create_db_session() as session:
            master_id = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none().id
            u = models.User(username=username,
                            hashed_password=get_password_hash(password),
                            permissions=permissions,
                            master_id=master_id)
            session.add(u)
            session.commit()
            session.refresh(u)
            p = {'id': u.id}
            r = client.request('DELETE', '/admin/users/interact_user', json=p, headers=auth)
            assert r.status_code == 200
            assert r.json()['success']

# class TestUserPermissions(BaseTestCleanDb):
