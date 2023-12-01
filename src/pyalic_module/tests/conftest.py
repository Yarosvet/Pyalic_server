"""Pytest configuration file for pyalic_module tests"""
from threading import Thread
from http.server import HTTPServer
import ssl
import pytest

from .server_http import preconfigured_handler_factory, PreconfiguredHTTPRequestHandler
from . import SERVER_PORT, CERT_FILE, KEY_FILE


@pytest.fixture(scope="function")
def http_server() -> PreconfiguredHTTPRequestHandler:
    """Configure HTTP server existing during per function runs"""
    handler = preconfigured_handler_factory()
    s = HTTPServer(("localhost", SERVER_PORT), handler)
    t = Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield handler
    s.shutdown()
    t.join()


@pytest.fixture(scope="function")
def ssl_server() -> PreconfiguredHTTPRequestHandler:
    """Configure HTTPS server existing during per function runs"""
    handler = preconfigured_handler_factory()
    s = HTTPServer(("localhost", SERVER_PORT), handler)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(CERT_FILE, KEY_FILE)
    s.socket = ssl_context.wrap_socket(s.socket, server_side=True)
    t = Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield handler
    s.shutdown()
    t.join()
