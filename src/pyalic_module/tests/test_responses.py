"""Test responses processing"""
from ..pyalic import response

# pylint: disable=missing-function-docstring

_wrong_request_content = {
    "detail": [
        {
            "type": "json_invalid",
            "loc": [
                "body",
                30
            ],
            "msg": "JSON decode error",
            "input": {},
            "ctx": {
                "error": "Expecting property name enclosed in double quotes"
            }
        }
    ]
}


def test_valid_key():
    content = {"success": True,
               "session_id": "123",
               "additional_content_product": "test_product",
               "additional_content_signature": "test_signature"}
    r = response.process_check_key(200, content)
    assert r.success
    assert r.session_id == "123"
    assert r.additional_content_product == "test_product"
    assert r.additional_content_signature == "test_signature"
    assert r.request_code == 200
    assert r.content == content
    assert r.error is None


def test_wrong_key_error():
    content = {"success": False,
               "error": "Invalid license key"}
    r = response.process_check_key(200, content)
    assert not r.success
    assert r.session_id is None
    assert r.additional_content_product == ""
    assert r.additional_content_signature == ""
    assert r.request_code == 200
    assert r.content == content
    assert r.error == "Invalid license key"


def test_check_key_wrong_request():
    content = _wrong_request_content
    r = response.process_check_key(422, content)
    assert not r.success
    assert r.session_id is None
    assert r.additional_content_product == ""
    assert r.additional_content_signature == ""
    assert r.request_code == 422
    assert r.content == content
    assert "Expecting property name enclosed in double quotes" in r.error


def test_keepalive_success():
    content = {"success": True}
    r = response.process_keepalive(200, content)
    assert r.success
    assert r.request_code == 200
    assert r.content == content
    assert r.error is None


def test_keepalive_fail():
    content = {"success": False,
               "error": "Session not found"}
    r = response.process_keepalive(404, content)
    assert not r.success
    assert r.request_code == 404
    assert r.content == content
    assert r.error == content['error']


def test_keepalive_wrong_request():
    content = _wrong_request_content
    r = response.process_keepalive(422, content)
    assert not r.success
    assert r.request_code == 422
    assert r.content == content
    assert "Expecting property name enclosed in double quotes" in r.error


def test_end_session_success():
    content = {"success": True}
    r = response.process_end_session(200, content)
    assert r.success
    assert r.request_code == 200
    assert r.content == content
    assert r.error is None


def test_end_session_fail():
    content = {"success": False,
               "error": "Session not found"}
    r = response.process_end_session(404, content)
    assert not r.success
    assert r.request_code == 404
    assert r.content == content
    assert r.error == content['error']


def test_end_session_wrong_request():
    content = _wrong_request_content
    r = response.process_end_session(422, content)
    assert not r.success
    assert r.request_code == 422
    assert r.content == content
    assert "Expecting property name enclosed in double quotes" in r.error
