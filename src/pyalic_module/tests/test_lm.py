"""Test License Manager module"""
import time

from ..pyalic.lm import LicenseManager
from ..pyalic.fingerprint import get_fingerprint
from . import SERVER_PORT, rand_str, CERT_FILE
from .server_http import HTTPRequest, HTTPResponse


def test_check_key_valid(ssl_server):
    """Test checking valid key"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.ENABLE_AUTO_KEEPALIVE = False
    key = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/check_license",
                    request_data={"license_key": key, "fingerprint": get_fingerprint()}),
        HTTPResponse(response_data={"session_id": f"1:0:{rand_str(32)}",
                                    "additional_content_signature": "",
                                    "additional_content_product": "",
                                    "success": True},
                     response_code=200)
    )
    assert lm.check_key(key).success


def test_check_key_invalid(ssl_server):
    """Test checking invalid key"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.ENABLE_AUTO_KEEPALIVE = False
    key = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/check_license",
                    request_data={"license_key": key, "fingerprint": get_fingerprint()}),
        HTTPResponse(response_data={"error": "Invalid license key", "success": False}, response_code=200)
    )
    assert not lm.check_key(key).success


def test_keepalive(ssl_server):
    """Test sending keepalive packet"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/keepalive",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200)
    )
    assert lm.keep_alive().success


def test_keepalive_invalid(ssl_server):
    """Test sending keepalive packet with invalid session id"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/keepalive",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"detail": "Session not found"}, response_code=404)
    )
    assert not lm.keep_alive().success


def test_end_session(ssl_server):
    """Test ending session"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/end_session",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200)
    )
    assert lm.end_session().success


def test_end_session_invalid(ssl_server):
    """Test ending session with invalid session id"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/end_session",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"detail": "Session not found"}, response_code=404)
    )
    assert not lm.end_session().success


def test_auto_keepalive(ssl_server):
    """Test auto-sending keepalive packets mechanism"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.ENABLE_AUTO_KEEPALIVE = True
    lm.auto_keepalive_sender.INTERVAL = 0.5
    key = rand_str(16)
    session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/check_license",
                    request_data={"license_key": key, "fingerprint": get_fingerprint()}),
        HTTPResponse(response_data={"session_id": session_id,
                                    "additional_content_signature": "",
                                    "additional_content_product": "",
                                    "success": True},
                     response_code=200)
    )

    keepalive_count = 0

    def got_keepalive():
        nonlocal keepalive_count
        keepalive_count += 1
        print(f"Got keepalive {keepalive_count}")

    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/keepalive",
                    request_data={"session_id": session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200),
        event=got_keepalive
    )
    check_resp = lm.check_key(key)
    assert check_resp.success
    assert lm.auto_keepalive_sender.alive
    time.sleep(2)
    assert keepalive_count >= 4
    lm.auto_keepalive_sender.stop()
    time.sleep(lm.auto_keepalive_sender.INTERVAL)
    assert not lm.auto_keepalive_sender.alive


def test_auto_keepalive_fail_event(ssl_server):
    """Test auto-sending keepalive packets mechanism with invalid session id"""
    lm = LicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.ENABLE_AUTO_KEEPALIVE = True
    lm.auto_keepalive_sender.INTERVAL = 0.5
    bad_flag = False

    def got_bad_keepalive(operation_response, exc):  # pylint: disable=unused-argument
        nonlocal bad_flag
        bad_flag = True

    lm.auto_keepalive_sender.set_event_bad_keepalive(got_bad_keepalive)
    key = rand_str(16)
    session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/check_license",
                    request_data={"license_key": key, "fingerprint": get_fingerprint()}),
        HTTPResponse(response_data={"session_id": session_id,
                                    "additional_content_signature": "",
                                    "additional_content_product": "",
                                    "success": True},
                     response_code=200)
    )
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/keepalive",
                    request_data={"session_id": session_id}),
        HTTPResponse(response_data={"detail": "Session not found"},
                     response_code=404)
    )
    check_resp = lm.check_key(key)
    assert check_resp.success
    time.sleep(lm.auto_keepalive_sender.INTERVAL)
    assert not lm.auto_keepalive_sender.alive
    assert bad_flag
