"""
Test operations with products and all related to it
"""
from dataclasses import dataclass
import pytest

from ..app import config
from ..app.db import models

from . import rand_str, create_db_session


# pylint: disable=duplicate-code

@dataclass
class RandProduct:  # pylint: disable=missing-class-docstring
    id: int
    name: str


def _create_rand_product() -> RandProduct:
    with create_db_session() as session:
        u = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none()
        p = models.Product(name=rand_str(16))
        p.owners.append(u)
        session.add(p)
        session.commit()
        session.refresh(p)
    return RandProduct(id=p.id, name=p.name)


def _create_rand_signature(product_id: int = None, license_key: str = None) -> int:
    if product_id is None:
        product_id = _create_rand_product().id
    if license_key is None:
        license_key = rand_str(32)
    with create_db_session() as session:
        s = models.Signature(license_key=license_key, product_id=product_id)
        session.add(s)
        session.commit()
        session.refresh(s)
    return s.id


# pylint: disable=C0116

@pytest.mark.usefixtures('client', 'rebuild_db', 'auth')
class TestProductsOperations:
    """
    Test operations with products
    """

    def test_empty_list_products(self, client, auth):
        p = {
            "limit": 100,
            "offset": 0
        }
        r = client.request('GET', '/admin/list_products', params=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['items'] == len(r.json()['products']) == 0

    def test_filled_list_products(self, client, auth):
        _create_rand_product()
        p = {
            "limit": 100,
            "offset": 0
        }
        r = client.request('GET', '/admin/list_products', params=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['items'] == len(r.json()['products']) == 1

    def test_add_product_all_fields(self, client, auth):
        name = rand_str(16)
        i_limit = 2
        s_limit = 3
        s_period = 60
        a_content = rand_str(32)
        p = {
            "name": name,
            "sig_install_limit": i_limit,
            "sig_sessions_limit": s_limit,
            "sig_period": s_period,
            "additional_content": a_content
        }
        r = client.request('POST', '/admin/product', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['name'] == name
        assert j['sig_install_limit'] == i_limit
        assert j['sig_sessions_limit'] == s_limit
        assert j['sig_period'] == s_period
        assert j['additional_content'] == a_content

    def test_add_product_autofill_fields(self, client, auth):
        name = rand_str(16)
        p = {
            "name": name
        }
        r = client.request('POST', '/admin/product', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['name'] == name
        assert j['sig_install_limit'] is None
        assert j['sig_sessions_limit'] is None
        assert j['sig_period'] is None
        assert j['additional_content'] == ""

    def test_add_product_name_exists(self, client, auth):
        product_name = _create_rand_product().name
        p = {
            "name": product_name
        }
        r = client.request('POST', '/admin/product', json=p, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Product with specified name already exists'}

    def test_update_product_full_fields(self, client, auth):
        product_id = _create_rand_product().id
        name = rand_str(16)
        i_limit = 2
        s_limit = 3
        s_period = 60
        a_content = rand_str(32)
        p = {
            "name": name,
            "sig_install_limit": i_limit,
            "sig_sessions_limit": s_limit,
            "sig_period": s_period,
            "additional_content": a_content
        }
        r = client.request('PUT', '/admin/product', json=p, params={'id': product_id}, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['name'] == name
        assert j['sig_install_limit'] == i_limit
        assert j['sig_sessions_limit'] == s_limit
        assert j['sig_period'] == s_period
        assert j['additional_content'] == a_content

    def test_update_product_only_fields(self, client, auth):
        product_id = _create_rand_product().id
        name = rand_str(16)
        p = {
            "name": name
        }
        r = client.request('PUT', '/admin/product', json=p, params={'id': product_id}, headers=auth)
        j = r.json()
        assert r.status_code == 200
        assert j['name'] == name

    def test_update_product_fill_sequentially(self, client, auth):
        """By the fact it tests `UnspecifiedModel` schema. It mustn't store any values of another instance."""
        product_id1 = _create_rand_product().id
        product_id2 = _create_rand_product().id
        product_id3 = _create_rand_product().id
        p1 = {
            "name": rand_str(16),
            "sig_install_limit": 2,
            "sig_sessions_limit": 3,
            "sig_period": 60,
            "additional_content": rand_str(32)
        }
        p2 = {
            "name": rand_str(16)
        }
        p3 = {
            "name": rand_str(16),
            "sig_install_limit": 2,
            "sig_sessions_limit": 3,
            "sig_period": 60,
            "additional_content": rand_str(32)
        }
        r = client.request('PUT', '/admin/product', json=p1, params={'id': product_id1}, headers=auth)
        assert r.status_code == 200
        j1 = r.json()
        r = client.request('PUT', '/admin/product', json=p2, params={'id': product_id2}, headers=auth)
        assert r.status_code == 200
        j2 = r.json()
        r = client.request('PUT', '/admin/product', json=p3, params={'id': product_id3}, headers=auth)
        assert r.status_code == 200
        j3 = r.json()
        assert j1['sig_install_limit'] != j2['sig_install_limit'] != j3['sig_install_limit']
        assert j1['sig_sessions_limit'] != j2['sig_sessions_limit'] != j3['sig_sessions_limit']
        assert j1['sig_period'] != j2['sig_period'] != j3['sig_period']
        assert j1['additional_content'] != j2['additional_content'] != j3['additional_content']

    def test_update_product_name_exists(self, client, auth):
        product_id = _create_rand_product().id
        another_product_name = _create_rand_product().name
        p = {
            "name": another_product_name
        }
        r = client.request('PUT', '/admin/product', json=p, params={'id': product_id}, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Product with specified name already exists'}

    def test_get_product_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('GET', '/admin/product', params=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Product not found'}

    def test_get_product(self, client, auth):
        product_id = _create_rand_product().id
        p = {
            "id": product_id
        }
        r = client.request('GET', '/admin/product', params=p, headers=auth)
        assert r.status_code == 200 and r.json()['id'] == product_id

    def test_delete_product(self, client, auth):
        product_id = _create_rand_product().id
        p = {
            "id": product_id
        }
        r = client.request('DELETE', '/admin/product', params=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}

    def test_delete_product_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('DELETE', '/admin/product', params=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Product not found'}

    def test_delete_product_with_signatures(self, client, auth):
        product_id = _create_rand_product().id
        _create_rand_signature(product_id)
        p = {
            "id": product_id
        }
        r = client.request('DELETE', '/admin/product', params=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}


class TestSignaturesOperations:
    """
    Test operations with signatures
    """

    def test_empty_list_signatures(self, client, auth):
        product_id = _create_rand_product().id
        p = {
            "product_id": product_id
        }
        r = client.request('GET', '/admin/list_signatures', params=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['items'] == len(r.json()['signatures']) == 0
        assert r.json()['product_id'] == product_id

    def test_filled_list_signatures(self, client, auth):
        product_id = _create_rand_product().id
        _create_rand_signature(product_id)
        p = {
            "product_id": product_id,
            "limit": 100,
            "offset": 0
        }
        r = client.request('GET', '/admin/list_signatures', params=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['items'] == len(r.json()['signatures']) == 1
        assert r.json()['product_id'] == product_id

    def test_add_signature_product_not_exists(self, client, auth):
        p = {
            "product_id": 0,
            "license_key": rand_str(32)
        }
        r = client.request('POST', '/admin/signature', json=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Product not found'}

    def test_add_signature_only_fields(self, client, auth):
        product_id = _create_rand_product().id
        key = rand_str(32)
        p = {
            "product_id": product_id,
            "license_key": key
        }
        r = client.request('POST', '/admin/signature', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['product_id'] == product_id
        assert j['comment'] == ""
        assert j['license_key'] == key
        assert j['additional_content'] == ""
        assert j['installed'] == 0
        assert j['activation_date'] is None

    def test_add_signature_not_activated_full_fields(self, client, auth):
        product_id = _create_rand_product().id
        key = rand_str(32)
        comment = rand_str(16)
        a_content = rand_str(32)
        p = {
            "product_id": product_id,
            "license_key": key,
            "comment": comment,
            "additional_content": a_content,
            "activate": False
        }
        r = client.request('POST', '/admin/signature', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['product_id'] == product_id
        assert j['comment'] == comment
        assert j['license_key'] == key
        assert j['additional_content'] == a_content
        assert j['installed'] == 0
        assert j['activation_date'] is None

    def test_add_signature_activated(self, client, auth):
        product_id = _create_rand_product().id
        p = {
            "product_id": product_id,
            "license_key": rand_str(32),
            "activate": True
        }
        r = client.request('POST', '/admin/signature', json=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['activation_date'] is not None

    def test_add_signature_already_exists(self, client, auth):
        key = rand_str(32)
        product_id = _create_rand_product().id
        _create_rand_signature(product_id=product_id, license_key=key)
        p = {
            "product_id": product_id,
            "license_key": key
        }
        r = client.request('POST', '/admin/signature', json=p, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Signature with specified license key already exists'}

    def test_update_signature_not_exists(self, client, auth):
        p = {
            "license_key": rand_str(32),
        }
        r = client.request('PUT', '/admin/signature', json=p, params={'id': 0}, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Signature not found'}

    def test_update_signature_full_fields(self, client, auth):
        signature_id = _create_rand_signature()
        key = rand_str(32)
        comment = rand_str(16)
        a_content = rand_str(32)
        p = {
            "license_key": key,
            "comment": comment,
            "additional_content": a_content
        }
        r = client.request('PUT', '/admin/signature', json=p, params={'id': signature_id}, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['comment'] == comment
        assert j['license_key'] == key
        assert j['additional_content'] == a_content

    def test_update_signature_only_fields(self, client, auth):
        signature_id = _create_rand_signature()
        key = rand_str(32)
        p = {
            "license_key": key
        }
        r = client.request('PUT', '/admin/signature', json=p, params={'id': signature_id}, headers=auth)
        assert r.status_code == 200
        assert r.json()['license_key'] == key

    def test_update_signature_already_exists(self, client, auth):
        key = rand_str(32)
        signature_id = _create_rand_signature(license_key=key)
        other_key = rand_str(32)
        _create_rand_signature(license_key=other_key)
        p = {
            "license_key": other_key
        }
        r = client.request('PUT', '/admin/signature', json=p, params={'id': signature_id}, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Signature with specified license key already exists'}

    def test_get_signature(self, client, auth):
        signature_id = _create_rand_signature()
        p = {
            "id": signature_id
        }
        r = client.request('GET', '/admin/signature', params=p, headers=auth)
        assert r.status_code == 200 and r.json()['id'] == signature_id

    def test_get_signature_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('GET', '/admin/signature', params=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Signature not found'}

    def test_delete_signature(self, client, auth):
        signature_id = _create_rand_signature()
        p = {
            "id": signature_id
        }
        r = client.request('DELETE', '/admin/signature', params=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}

    def test_delete_signature_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('DELETE', '/admin/signature', params=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Signature not found'}

    def test_delete_signature_with_installations(self, client, auth):
        signature_id = _create_rand_signature()
        with create_db_session() as session:
            inst = models.Installation(fingerprint=rand_str(16), signature_id=signature_id)
            session.add(inst)
            session.commit()
        p = {
            "id": signature_id
        }
        r = client.request('DELETE', '/admin/signature', params=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}
