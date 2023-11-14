import pytest

from src.pyAdvancedLic_Server.app import config
from src.pyAdvancedLic_Server.app.db import models

from . import rand_str, create_db_session


def _create_rand_product() -> tuple[int, str]:
    with create_db_session() as session:
        u = session.query(models.User).filter_by(username=config.DEFAULT_USER).one_or_none()
        p = models.Product(name=rand_str(16))
        p.owners.append(u)
        session.add(p)
        session.commit()
        session.refresh(p)
    return p.id, p.name


def _create_rand_signature(product_id: int = None, license_key: str = None) -> int:
    if product_id is None:
        product_id = _create_rand_product()[0]
    if license_key is None:
        license_key = rand_str(32)
    with create_db_session() as session:
        s = models.Signature(license_key=license_key, product_id=product_id)
        session.add(s)
        session.commit()
        session.refresh(s)
    return s.id


@pytest.mark.usefixtures('client', 'rebuild_db', 'auth')
class TestProductsOperations:
    def test_empty_list_products(self, client, auth):
        p = {
            "limit": 100,
            "offset": 0
        }
        r = client.request('GET', '/admin/list_products', json=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['items'] == len(r.json()['products']) == 0

    def test_filled_list_products(self, client, auth):
        _create_rand_product()
        p = {
            "limit": 100,
            "offset": 0
        }
        r = client.request('GET', '/admin/list_products', json=p, headers=auth)
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
        r = client.request('POST', '/admin/interact_product', json=p, headers=auth)
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
        r = client.request('POST', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['name'] == name
        assert j['sig_install_limit'] is None
        assert j['sig_sessions_limit'] is None
        assert j['sig_period'] is None
        assert j['additional_content'] == ""

    def test_add_product_name_exists(self, client, auth):
        product_id, product_name = _create_rand_product()
        p = {
            "name": product_name
        }
        r = client.request('POST', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Product with specified name already exists'}

    def test_update_product_full_fields(self, client, auth):
        product_id, product_name = _create_rand_product()
        name = rand_str(16)
        i_limit = 2
        s_limit = 3
        s_period = 60
        a_content = rand_str(32)
        p = {
            "id": product_id,
            "name": name,
            "sig_install_limit": i_limit,
            "sig_sessions_limit": s_limit,
            "sig_period": s_period,
            "additional_content": a_content
        }
        r = client.request('PUT', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['name'] == name
        assert j['sig_install_limit'] == i_limit
        assert j['sig_sessions_limit'] == s_limit
        assert j['sig_period'] == s_period
        assert j['additional_content'] == a_content

    def test_update_product_only_fields(self, client, auth):
        product_id, product_name = _create_rand_product()
        name = rand_str(16)
        p = {
            "id": product_id,
            "name": name
        }
        r = client.request('PUT', '/admin/interact_product', json=p, headers=auth)
        j = r.json()
        assert r.status_code == 200
        assert j['name'] == name

    def test_update_product_fill_sequentially(self, client, auth):
        product_id1, product_name1 = _create_rand_product()
        product_id2, product_name2 = _create_rand_product()
        product_id3, product_name3 = _create_rand_product()
        p1 = {
            "id": product_id1,
            "name": rand_str(16),
            "sig_install_limit": 2,
            "sig_sessions_limit": 3,
            "sig_period": 60,
            "additional_content": rand_str(32)
        }
        p2 = {
            "id": product_id2,
            "name": rand_str(16)
        }
        p3 = {
            "id": product_id3,
            "name": rand_str(16),
            "sig_install_limit": 2,
            "sig_sessions_limit": 3,
            "sig_period": 60,
            "additional_content": rand_str(32)
        }
        r = client.request('PUT', '/admin/interact_product', json=p1, headers=auth)
        assert r.status_code == 200
        j1 = r.json()
        r = client.request('PUT', '/admin/interact_product', json=p2, headers=auth)
        assert r.status_code == 200
        j2 = r.json()
        r = client.request('PUT', '/admin/interact_product', json=p3, headers=auth)
        assert r.status_code == 200
        j3 = r.json()
        assert j1['sig_install_limit'] != j2['sig_install_limit'] != j3['sig_install_limit']
        assert j1['sig_sessions_limit'] != j2['sig_sessions_limit'] != j3['sig_sessions_limit']
        assert j1['sig_period'] != j2['sig_period'] != j3['sig_period']
        assert j1['additional_content'] != j2['additional_content'] != j3['additional_content']

    def test_update_product_name_exists(self, client, auth):
        product_id, product_name = _create_rand_product()
        another_product_id, another_product_name = _create_rand_product()
        p = {
            "id": product_id,
            "name": another_product_name
        }
        r = client.request('PUT', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Product with specified name already exists'}

    def test_get_product_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('GET', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Product not found'}

    def test_get_product(self, client, auth):
        product_id, product_name = _create_rand_product()
        p = {
            "id": product_id
        }
        r = client.request('GET', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200 and r.json()['id'] == product_id

    def test_delete_product(self, client, auth):
        product_id, product_name = _create_rand_product()
        p = {
            "id": product_id
        }
        r = client.request('DELETE', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}

    def test_delete_product_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('DELETE', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Product not found'}

    def test_delete_product_with_signatures(self, client, auth):
        product_id, product_name = _create_rand_product()
        _create_rand_signature(product_id)
        p = {
            "id": product_id
        }
        r = client.request('DELETE', '/admin/interact_product', json=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}


class TestSignaturesOperations:
    def test_empty_list_signatures(self, client, auth):
        product_id, product_name = _create_rand_product()
        p = {
            "product_id": product_id,
            "limit": 100,
            "offset": 0
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['items'] == len(r.json()['signatures']) == 0
        assert r.json()['product_id'] == product_id

    def test_filled_list_signatures(self, client, auth):
        product_id, product_name = _create_rand_product()
        _create_rand_signature(product_id)
        p = {
            "product_id": product_id,
            "limit": 100,
            "offset": 0
        }
        r = client.request('GET', '/admin/list_signatures', json=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['items'] == len(r.json()['signatures']) == 1
        assert r.json()['product_id'] == product_id

    def test_add_signature_product_not_exists(self, client, auth):
        p = {
            "product_id": 0,
            "license_key": rand_str(32)
        }
        r = client.request('POST', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Product not found'}

    def test_add_signature_only_fields(self, client, auth):
        product_id, product_name = _create_rand_product()
        key = rand_str(32)
        p = {
            "product_id": product_id,
            "license_key": key
        }
        r = client.request('POST', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['product_id'] == product_id
        assert j['comment'] == ""
        assert j['license_key'] == key
        assert j['additional_content'] == ""
        assert j['installed'] == 0
        assert j['activation_date'] is None

    def test_add_signature_not_activated_full_fields(self, client, auth):
        product_id, product_name = _create_rand_product()
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
        r = client.request('POST', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['product_id'] == product_id
        assert j['comment'] == comment
        assert j['license_key'] == key
        assert j['additional_content'] == a_content
        assert j['installed'] == 0
        assert j['activation_date'] is None

    def test_add_signature_activated(self, client, auth):
        product_id, product_name = _create_rand_product()
        p = {
            "product_id": product_id,
            "license_key": rand_str(32),
            "activate": True
        }
        r = client.request('POST', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['activation_date'] is not None

    def test_add_signature_already_exists(self, client, auth):
        key = rand_str(32)
        product_id, product_name = _create_rand_product()
        _create_rand_signature(product_id=product_id, license_key=key)
        p = {
            "product_id": product_id,
            "license_key": key
        }
        r = client.request('POST', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Signature with specified license key already exists'}

    def test_update_signature_not_exists(self, client, auth):
        p = {
            "id": 0,
            "license_key": rand_str(32),
        }
        r = client.request('PUT', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Signature not found'}

    def test_update_signature_full_fields(self, client, auth):
        signature_id = _create_rand_signature()
        key = rand_str(32)
        comment = rand_str(16)
        a_content = rand_str(32)
        p = {
            "id": signature_id,
            "license_key": key,
            "comment": comment,
            "additional_content": a_content
        }
        r = client.request('PUT', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200
        j = r.json()
        assert j['comment'] == comment
        assert j['license_key'] == key
        assert j['additional_content'] == a_content

    def test_update_signature_only_fields(self, client, auth):
        signature_id = _create_rand_signature()
        key = rand_str(32)
        p = {
            "id": signature_id,
            "license_key": key
        }
        r = client.request('PUT', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200
        assert r.json()['license_key'] == key

    def test_update_signature_already_exists(self, client, auth):
        key = rand_str(32)
        signature_id = _create_rand_signature(license_key=key)
        other_key = rand_str(32)
        _create_rand_signature(license_key=other_key)
        p = {
            "id": signature_id,
            "license_key": other_key
        }
        r = client.request('PUT', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 400 and r.json() == {'detail': 'Signature with specified license key already exists'}

    def test_get_signature(self, client, auth):
        signature_id = _create_rand_signature()
        p = {
            "id": signature_id
        }
        r = client.request('GET', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200 and r.json()['id'] == signature_id

    def test_get_signature_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('GET', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 404 and r.json() == {'detail': 'Signature not found'}

    def test_delete_signature(self, client, auth):
        signature_id = _create_rand_signature()
        p = {
            "id": signature_id
        }
        r = client.request('DELETE', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}

    def test_delete_signature_not_exists(self, client, auth):
        p = {
            "id": 0
        }
        r = client.request('DELETE', '/admin/interact_signature', json=p, headers=auth)
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
        r = client.request('DELETE', '/admin/interact_signature', json=p, headers=auth)
        assert r.status_code == 200 and r.json() == {'success': True}
