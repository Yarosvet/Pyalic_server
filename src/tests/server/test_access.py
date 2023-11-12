import pytest
from fastapi.testclient import TestClient

from src.pyAdvancedLic_Server.app import config
from src.pyAdvancedLic_Server.app.db import models
from src.pyAdvancedLic_Server.app.access.auth import check_password
from src.pyAdvancedLic_Server.app.access.auth import get_password_hash

from . import rand_str, create_db_session


def _create_rand_product_with_user() -> int:
    with create_db_session() as session:
        # Create user
        u = models.User(username=rand_str(16), hashed_password=get_password_hash(rand_str(16)))
        session.add(u)
        session.commit()
        session.refresh(u)
        # Create a product
        p = models.Product(name=rand_str(16))
        p.owners.append(u)
        session.add(p)
        session.commit()
        session.refresh(p)
    return p.id


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
        assert r.json()['items'] == len(r.json()['users'])

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

    def test_get_user_not_exists(self, client, auth):
        p = {'id': 0}
        r = client.request('GET', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 404 and r.json()['detail'] == 'User not found'

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

    def test_update_user_not_exists(self, client, auth):
        p = {
            'id': 0,
            'username': rand_str(16)
        }
        r = client.request('PUT', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 404 and r.json()['detail'] == 'User not found'

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

    def test_delete_user_not_exists(self, client, auth):
        p = {'id': 0}
        r = client.request('DELETE', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 404 and r.json()['detail'] == 'User not found'


@pytest.mark.usefixtures('client', 'rebuild_db', 'auth')
class TestUserPermissions:

    @staticmethod
    def __set_default_user_permissions(permissions: str):
        with create_db_session() as session:
            u = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none()
            u.permissions = permissions
            session.commit()

    @staticmethod
    def __new_user_auth(permissions: str, client: TestClient, attach_master=True) -> dict[str, str]:
        with create_db_session() as session:
            master_id = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none().id
            username = rand_str(16)
            password = rand_str(16)
            u = models.User(master_id=master_id if attach_master else None,
                            permissions=permissions,
                            username=username,
                            hashed_password=get_password_hash(password))
            session.add(u)
            session.commit()
            p = {
                "grant_type": "password",
                "username": username,
                "password": password
            }
            r = client.request('POST', '/admin/token', data=p)
            token = r.json()['access_token']
            return {'Authorization': f"Bearer {token}"}

    def test_permissions_inheritance(self, client, auth):
        self.__set_default_user_permissions("manage_own_products,manage_other_products,create_users")
        p = {
            "username": rand_str(16),
            "password": rand_str(16),
            "permissions": "manage_own_products,manage_other_products"
        }
        r = client.request('POST', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 200

    def test_permissions_inheritance_abuse(self, client, auth):
        self.__set_default_user_permissions("manage_own_products,manage_other_products,create_users")
        p = {
            "username": rand_str(16),
            "password": rand_str(16),
            "permissions": "manage_own_products,manage_other_products,manage_other_users,create_users"
        }
        r = client.request('POST', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 403

    def test_manage_own_products(self, client, auth):
        self.__set_default_user_permissions("manage_own_products")
        p = {
            "name": "TestProductB",
            "sig_install_limit": 2,
            "sig_sessions_limit": 3
        }
        r = client.request('POST', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200
        p = {
            "product_id": r.json()['id'],
            "offset": 0,
            "limit": 100
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 200

    def test_manage_own_products_abuse(self, client, auth):
        self.__set_default_user_permissions("")
        p = {
            "name": "TestProductB",
            "sig_install_limit": 2,
            "sig_sessions_limit": 3
        }
        r = client.request('POST', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 403
        with create_db_session() as session:
            u = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none()
            p = models.Product(name=rand_str(16))
            p.owners.append(u)
            session.add(p)
            session.commit()
            session.refresh(p)
            p = {
                "product_id": p.id,
                "offset": 0,
                "limit": 100
            }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 403

    def test_manage_other_products_abuse(self, client, auth):
        product_id = _create_rand_product_with_user()
        # Set empty permissions
        self.__set_default_user_permissions("")
        # Try to get product
        p = {
            "id": product_id
        }
        r = client.request('GET', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 403  # Must fail
        # Try to get signatures of this product
        p = {
            "product_id": product_id,
            "offset": 0,
            "limit": 100
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 403  # Must fail
        # Try to update product
        p = {
            "product_id": product_id,
            "name": rand_str(16),
            "sig_install_limit": None
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 403  # Must fail

    def test_manage_other_products(self, client, auth):
        product_id = _create_rand_product_with_user()
        # Set permission
        self.__set_default_user_permissions("manage_other_products")
        # Try to get product
        p = {
            "id": product_id
        }
        r = client.request('GET', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200  # Must work
        # Try to get signatures of this product
        p = {
            "product_id": product_id,
            "offset": 0,
            "limit": 100
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 200  # Must work
        # Try to update product
        p = {
            "product_id": product_id,
            "name": "testProductC",
            "sig_install_limit": None
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 200  # Must work

    def test_read_other_products_abuse(self, client, auth):
        product_id = _create_rand_product_with_user()
        # Set empty permissions
        self.__set_default_user_permissions("")
        # Try to get product
        p = {
            "id": product_id
        }
        r = client.request('GET', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 403  # Must fail
        # Try to get signatures of this product
        p = {
            "product_id": product_id,
            "offset": 0,
            "limit": 100
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 403  # Must fail

    def test_read_other_products(self, client, auth):
        product_id = _create_rand_product_with_user()
        # Set permission
        self.__set_default_user_permissions("manage_other_products")
        # Try to get product
        p = {
            "id": product_id
        }
        r = client.request('GET', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200  # Must work
        # Try to get signatures of this product
        p = {
            "product_id": product_id,
            "offset": 0,
            "limit": 100
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 200  # Must work

    def test_create_users(self, client, auth):
        self.__set_default_user_permissions("create_users")
        p = {
            "username": rand_str(16),
            "password": rand_str(16),
            "permissions": ""
        }
        # Try to create a user
        r = client.request('POST', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 200  # Must work

    def test_create_users_abuse(self, client, auth):
        self.__set_default_user_permissions("")
        p = {
            "username": rand_str(16),
            "password": rand_str(16),
            "permissions": ""
        }
        # Try to create a user
        r = client.request('POST', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 403  # Must fail

    def test_manage_other_users(self, client, auth):
        self.__set_default_user_permissions("manage_other_users")
        # Create not owned user
        with create_db_session() as session:
            u = models.User(username=rand_str(16),
                            hashed_password=get_password_hash(rand_str(16)),
                            permissions="")
            session.add(u)
            session.commit()
            u_id = u.id
            p = {
                'id': u_id,
                'username': rand_str(16),
            }
        # Try to update him
        r = client.request('PUT', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 200  # Must work

    def test_manage_other_users_abuse(self, client, auth):
        self.__set_default_user_permissions("")
        # Create not owned user
        with create_db_session() as session:
            u = models.User(username=rand_str(16),
                            hashed_password=get_password_hash(rand_str(16)),
                            permissions="")
            session.add(u)
            session.commit()
            u_id = u.id
            p = {
                'id': u_id,
                'username': rand_str(16),
            }
        # Try to update him
        r = client.request('PUT', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 403  # Must fail

    def test_manage_own_users(self, client, auth):
        self.__set_default_user_permissions("manage_own_users")
        # Create owned user
        with create_db_session() as session:
            master_id = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none().id
            u = models.User(username=rand_str(16),
                            hashed_password=get_password_hash(rand_str(16)),
                            permissions="",
                            master_id=master_id)
            session.add(u)
            session.commit()
            u_id = u.id
        p = {
            'id': u_id,
            'username': rand_str(16),
        }
        # Try to update him
        r = client.request('PUT', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 200  # Must work

    def test_manage_own_users_abuse(self, client, auth):
        self.__set_default_user_permissions("")
        # Create owned user
        with create_db_session() as session:
            master_id = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none().id
            u = models.User(username=rand_str(16),
                            hashed_password=get_password_hash(rand_str(16)),
                            permissions="",
                            master_id=master_id)
            session.add(u)
            session.commit()
            u_id = u.id
        p = {
            'id': u_id,
            'username': rand_str(16),
        }
        # Try to update him
        r = client.request('PUT', '/admin/users/interact_user', json=p, headers=auth)
        assert r.status_code == 403  # Must fail
