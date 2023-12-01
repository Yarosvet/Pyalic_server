"""Test AsyncSecureApiWrapper class"""
import pytest

from ...pyalic.asyncio.wrappers import AsyncSecureApiWrapper
from .. import SERVER_PORT, rand_str, CERT_FILE
from ..server_http import HTTPRequest, HTTPResponse


# pylint: disable=duplicate-code

@pytest.mark.asyncio
async def test_async_check_key_secure(http_server):
    """Test checking key after one attempt failed"""
    key = rand_str(16)
    fingerprint = rand_str(16)
    http_server.fail_first = True
    http_server.set_response(
        HTTPRequest(method="GET",
                    url="/check_license",
                    request_data={"license_key": key, "fingerprint": fingerprint}),
        HTTPResponse(response_data={"session_id": f"1:0:{rand_str(32)}",
                                    "additional_content_signature": "",
                                    "additional_content_product": "",
                                    "success": True},
                     response_code=200),
    )
    wrapper = AsyncSecureApiWrapper(f"http://localhost:{SERVER_PORT}", False)
    check_resp = await wrapper.check_key(key, fingerprint)
    assert check_resp.json()["success"]


@pytest.mark.asyncio
async def test_check_key_ssl_enabled(ssl_server):
    """Test checking key with SSL enabled"""
    key = rand_str(16)
    fingerprint = rand_str(16)
    ssl_server.set_response(
        HTTPRequest(method="GET",
                    url="/check_license",
                    request_data={"license_key": key, "fingerprint": fingerprint}),
        HTTPResponse(response_data={"session_id": f"1:0:{rand_str(32)}",
                                    "additional_content_signature": "",
                                    "additional_content_product": "",
                                    "success": True},
                     response_code=200),
    )
    wrapper = AsyncSecureApiWrapper(f"https://localhost:{SERVER_PORT}", CERT_FILE)
    check_resp = await wrapper.check_key(key, fingerprint)
    assert check_resp.json()["success"]


@pytest.mark.asyncio
async def test_keepalive_secure(http_server):
    """Test sending keepalive packet after one attempt failed"""
    session_id = rand_str(16)
    http_server.fail_first = True
    http_server.set_response(
        HTTPRequest(method="POST",
                    url="/keepalive",
                    request_data={"session_id": session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200),
    )
    wrapper = AsyncSecureApiWrapper(f"http://localhost:{SERVER_PORT}", False)
    keepalive_resp = await wrapper.keepalive(session_id)
    assert keepalive_resp.json()["success"]


@pytest.mark.asyncio
async def test_end_session_secure(http_server):
    """Test sending end session packet after one attempt failed"""
    session_id = rand_str(16)
    http_server.fail_first = True
    http_server.set_response(
        HTTPRequest(method="POST",
                    url="/end_session",
                    request_data={"session_id": session_id}),
        HTTPResponse(response_data={"success": True},
                     response_code=200),
    )
    wrapper = AsyncSecureApiWrapper(f"http://localhost:{SERVER_PORT}", False)
    end_session_resp = await wrapper.end_session(session_id)
    assert end_session_resp.json()["success"]
