"""Test Async License Manager module"""
import asyncio
import pytest

from ...pyalic.asyncio.lm import AsyncLicenseManager
from ...pyalic.fingerprint import get_fingerprint
from .. import SERVER_PORT, rand_str, CERT_FILE
from ..server_http import HTTPRequest, HTTPResponse


# pylint: disable=duplicate-code

@pytest.mark.asyncio
async def test_check_key_valid(ssl_server):
    """Test checking valid key"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
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
    assert (await lm.check_key(key)).success


@pytest.mark.asyncio
async def test_check_key_invalid(ssl_server):
    """Test checking invalid key"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.ENABLE_AUTO_KEEPALIVE = False
    key = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/check_license",
                    request_data={"license_key": key, "fingerprint": get_fingerprint()}),
        HTTPResponse(response_data={"error": "Invalid license key", "success": False}, response_code=403)
    )
    assert not (await lm.check_key(key)).success


@pytest.mark.asyncio
async def test_keepalive(ssl_server):
    """Test sending keepalive packet"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/keepalive",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200)
    )
    assert (await lm.keep_alive()).success


@pytest.mark.asyncio
async def test_keepalive_invalid(ssl_server):
    """Test sending keepalive packet with invalid session id"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/keepalive",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"detail": "Session not found"}, response_code=404)
    )
    assert not (await lm.keep_alive()).success


@pytest.mark.asyncio
async def test_end_session(ssl_server):
    """Test ending session"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/end_session",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200)
    )
    assert (await lm.end_session()).success


@pytest.mark.asyncio
async def test_end_session_invalid(ssl_server):
    """Test ending session with invalid session id"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    lm.session_id = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/end_session",
                    request_data={"session_id": lm.session_id}),
        HTTPResponse(response_data={"detail": "Session not found"}, response_code=404)
    )
    assert not (await lm.end_session()).success


@pytest.mark.asyncio
async def test_auto_keepalive(ssl_server):
    """Test auto-sending keepalive packets mechanism"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
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

    ssl_server.set_response(
        HTTPRequest(method="POST",
                    url="/keepalive",
                    request_data={"session_id": session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200),
        event=got_keepalive
    )
    check_resp = await lm.check_key(key)
    assert check_resp.success
    await asyncio.sleep(2)
    assert keepalive_count >= 4
    lm.auto_keepalive_sender.stop()
    await asyncio.sleep(lm.auto_keepalive_sender.INTERVAL)
    assert not lm.auto_keepalive_sender.alive


@pytest.mark.asyncio
async def test_auto_keepalive_fail_event(ssl_server):
    """Test auto-sending keepalive packets mechanism with invalid session id"""
    lm = AsyncLicenseManager(f"https://localhost:{SERVER_PORT}", CERT_FILE)
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
        HTTPRequest(method="POST",
                    url="/keepalive",
                    request_data={"session_id": session_id}),
        HTTPResponse(response_data={"detail": "Session not found"},
                     response_code=404)
    )
    check_resp = await lm.check_key(key)
    assert check_resp.success
    await asyncio.sleep(lm.auto_keepalive_sender.INTERVAL)
    assert bad_flag
