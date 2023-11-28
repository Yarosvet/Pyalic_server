"""Wrapper for API"""
import requests

from .exceptions import RequestFailed


# pylint: disable=duplicate-code

class ApiWrapper:
    """Pyalic API wrapper"""

    TIMEOUT = 20

    def __init__(self, url: str, ssl_pkey: str):
        self.url = url
        self.ssl_pkey = ssl_pkey

    def check_key(self, key: str, fingerprint: str) -> requests.Response:
        """Send **check key** request"""
        return requests.get(f"{self.url}/check_license",
                            verify=self.ssl_pkey,
                            json={"license_key": key, "fingerprint": fingerprint},
                            timeout=self.TIMEOUT)

    def keepalive(self, session_id: str) -> requests.Response:
        """Send **keepalive** request"""
        return requests.get(f"{self.url}/keepalive",
                            verify=self.ssl_pkey,
                            json={"session_id": session_id},
                            timeout=self.TIMEOUT)

    def end_session(self, session_id: str) -> requests.Response:
        """Send **end session** request"""
        return requests.get(f"{self.url}/end_session",
                            verify=self.ssl_pkey,
                            json={"session_id": session_id},
                            timeout=self.TIMEOUT)


class SecureApiWrapper(ApiWrapper):
    """Secure Pyalic API wrapper which attempts to get response several times"""

    ATTEMPTS = 3

    def check_key(self, key: str, fingerprint: str) -> requests.Response:
        """Securely send **check key** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = super().check_key(key=key, fingerprint=fingerprint)
                r.json()
                return r
            except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    def keepalive(self, session_id: str) -> requests.Response:
        """Securely send **keepalive** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = super().keepalive(session_id)
                r.json()
                return r
            except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    def end_session(self, session_id: str) -> requests.Response:
        """Securely send **end session** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = super().end_session(session_id)
                r.json()
                return r
            except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception
