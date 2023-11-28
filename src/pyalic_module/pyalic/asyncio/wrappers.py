"""Asynchronous wrapper for API"""
import ssl
import json
import aiohttp

from ..exceptions import RequestFailed


# pylint: disable=duplicate-code

class AsyncApiWrapper:
    """Pyalic API asynchronous wrapper"""
    TIMEOUT = 20

    def __init__(self, url: str, ssl_ca: str | bool):
        self.url = url
        if ssl_ca:
            self.ssl_context = ssl.create_default_context(cafile=ssl_ca)
        else:
            self.ssl_context = False

    async def check_key(self, key: str, fingerprint: str) -> aiohttp.ClientResponse:
        """Send **check key** request"""
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context)) as session:
            return await session.request('GET',
                                         f"{self.url}/check_license",
                                         json={"license_key": key, "fingerprint": fingerprint})

    async def keepalive(self, session_id: str) -> aiohttp.ClientResponse:
        """Send **keepalive** request"""
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context)) as session:
            return await session.request('GET',
                                         f"{self.url}/keepalive",
                                         json={"session_id": session_id})

    async def end_session(self, session_id: str) -> aiohttp.ClientResponse:
        """Send **end session** request"""
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=self.ssl_context)) as session:
            return await session.request('GET',
                                         f"{self.url}/end_session",
                                         json={"session_id": session_id})


class AsyncSecureApiWrapper(AsyncApiWrapper):
    """Secure Pyalic API asynchronous wrapper which attempts to get response several times"""
    ATTEMPTS = 3

    async def check_key(self, key: str, fingerprint: str) -> aiohttp.ClientResponse:
        """Securely send **check key** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = await super().check_key(key=key, fingerprint=fingerprint)
                await r.json()
                return r
            except (aiohttp.ClientError, json.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    async def keepalive(self, session_id: str) -> aiohttp.ClientResponse:
        """Securely send **keepalive** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = await super().keepalive(session_id)
                await r.json()
                return r
            except (aiohttp.ClientError, json.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception

    async def end_session(self, session_id: str) -> aiohttp.ClientResponse:
        """Securely send **end session** request"""
        attempted = 0
        while True:
            attempted += 1
            try:
                r = await super().end_session(session_id)
                await r.json()
                return r
            except (aiohttp.ClientError, json.JSONDecodeError) as exc:
                if attempted < self.ATTEMPTS:
                    continue
                raise RequestFailed from exc  # If attempts limit reached, raise exception
