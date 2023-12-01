"""Wrapper for API"""
from json import JSONDecodeError
import httpx

from .exceptions import RequestFailed


# pylint: disable=duplicate-code

class ApiWrapper:
    """Pyalic API wrapper"""

    TIMEOUT = 20

    def __init__(self, url: str, ssl_cert: str | bool = False):
        self.url = url
        self.ssl_cert = ssl_cert

    def check_key(self, key: str, fingerprint: str) -> httpx.Response:
        """Send **check key** request"""
        return httpx.request('GET', f"{self.url}/check_license",
                             verify=self.ssl_cert,
                             json={"license_key": key, "fingerprint": fingerprint},
                             timeout=self.TIMEOUT)

    def keepalive(self, session_id: str) -> httpx.Response:
        """Send **keepalive** request"""
        return httpx.request('POST', f"{self.url}/keepalive",
                             verify=self.ssl_cert,
                             json={"session_id": session_id},
                             timeout=self.TIMEOUT)

    def end_session(self, session_id: str) -> httpx.Response:
        """Send **end session** request"""
        return httpx.request('POST', f"{self.url}/end_session",
                             verify=self.ssl_cert,
                             json={"session_id": session_id},
                             timeout=self.TIMEOUT)


class SecureApiWrapper(ApiWrapper):
    """Secure Pyalic API wrapper which attempts to get response several times"""

    ATTEMPTS = 3

    def check_key(self, key: str, fingerprint: str) -> httpx.Response:
        """Securely send **check key** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = super().check_key(key=key, fingerprint=fingerprint)
                r.json()
                return r
            except (httpx.RequestError, JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    def keepalive(self, session_id: str) -> httpx.Response:
        """Securely send **keepalive** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = super().keepalive(session_id)
                r.json()
                return r
            except (httpx.RequestError, JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    def end_session(self, session_id: str) -> httpx.Response:
        """Securely send **end session** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = super().end_session(session_id)
                r.json()
                return r
            except (httpx.RequestError, JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception
