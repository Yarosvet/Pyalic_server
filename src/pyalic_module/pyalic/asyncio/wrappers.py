"""Asynchronous wrapper for API"""
import ssl
import json
import httpx

from ..exceptions import RequestFailed


# pylint: disable=duplicate-code

class AsyncApiWrapper:
    """Pyalic API asynchronous wrapper"""
    TIMEOUT = 20

    def __init__(self, url: str, ssl_cert: str | bool):
        self.url = url
        if ssl_cert:
            self.ssl_context = ssl.create_default_context(cafile=ssl_cert)
        else:
            self.ssl_context = False

    async def check_key(self, key: str, fingerprint: str) -> httpx.Response:
        """Send **check key** request"""
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            return await client.request('GET',
                                        f"{self.url}/check_license",
                                        json={"license_key": key, "fingerprint": fingerprint})

    async def keepalive(self, client_id: str) -> httpx.Response:
        """Send **keepalive** request"""
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            return await client.request('GET',
                                        f"{self.url}/keepalive",
                                        json={"client_id": client_id})

    async def end_client(self, client_id: str) -> httpx.Response:
        """Send **end client** request"""
        async with httpx.AsyncClient(verify=self.ssl_context) as client:
            return await client.request('GET',
                                        f"{self.url}/end_client",
                                        json={"client_id": client_id})


class AsyncSecureApiWrapper(AsyncApiWrapper):
    """Secure Pyalic API asynchronous wrapper which attempts to get response several times"""
    ATTEMPTS = 3

    async def check_key(self, key: str, fingerprint: str) -> httpx.Response:
        """Securely send **check key** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = await super().check_key(key=key, fingerprint=fingerprint)
                r.json()
                return r
            except (httpx.RequestError, json.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    async def keepalive(self, client_id: str) -> httpx.Response:
        """Securely send **keepalive** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = await super().keepalive(client_id)
                await r.json()
                return r
            except (httpx.RequestError, json.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    async def end_session(self, client_id: str) -> httpx.Response:
        """Securely send **end client** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = await super().end_client(client_id)
                await r.json()
                return r
            except (httpx.RequestError, json.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception
