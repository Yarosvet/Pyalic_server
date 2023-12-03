"""AsyncLicenseManager's environment module"""
import asyncio
import typing
import time

from .. import response
from ..exceptions import RequestFailed
from .wrappers import AsyncSecureApiWrapper
from ..fingerprint import get_fingerprint


class CallableBadKeepaliveEventAsync(typing.Protocol):  # pylint: disable=missing-class-docstring
    def __call__(self,
                 operation_response: response.OperationResponse = None,
                 exc: Exception = None) -> typing.Awaitable:
        ...


class AsyncAutoKeepaliveSender:
    """Asynchronous automatic keep-alive packets sender"""

    interval = 2

    alive = False
    _stop_flag = False
    _t = None
    _event = None

    def __init__(self, async_lm: 'AsyncLicenseManager'):
        self.lm = async_lm

    def start(self):
        """
        Start sending keepalive packets in a new thread.
        If already started, it will stop existing thread and start a new one
        """
        if self.alive:
            return
        asyncio.ensure_future(self._keepalive_cycle(), loop=asyncio.get_event_loop())

    async def _keepalive_cycle(self):
        self.alive = True
        try:
            # Keepalive
            last_sent = time.time()
            resp = await self.lm.keep_alive()
            while resp.success and not self._stop_flag:
                # Keep interval between requests
                time_past = time.time() - last_sent
                await asyncio.sleep(self.interval - time_past if self.interval > time_past else 0)
                # Keepalive
                last_sent = time.time()
                resp = await self.lm.keep_alive()
            if not resp.success:
                await self._call_event_bad_keepalive(operation_response=resp)
        except RequestFailed as exc:
            # Call event if request failed
            await self._call_event_bad_keepalive(exc=exc)
        finally:
            self.alive = False

    def set_event_bad_keepalive(self, func: CallableBadKeepaliveEventAsync) -> None:
        """
        Set asynchronous function-event will be awaited when keep-alive request goes wrong.

        Function must expect two arguments:

        ``operation_response: OperationResponse = None, exc: Exception = None``

        It gets one of two arguments:
        operation_response, if request returned wrong answer
        exc, if something caused exception while trying to send request
        """
        self._event = func

    async def _call_event_bad_keepalive(self,
                                        operation_response: response.OperationResponse = None,
                                        exc: Exception = None) -> None:
        if self._event is not None:
            await self._event(operation_response=operation_response, exc=exc)

    def stop(self):
        """Stop sending keepalive packets"""
        self._stop_flag = True


class AsyncLicenseManager:
    """Asynchronous license manager"""

    enable_auto_keepalive = True

    def __init__(self, root_url: str, ssl_public_key: str | None = None):
        """
        Synchronous License Manager
        :param root_url: Root URL of pyAdvancedLic Server
        :param ssl_public_key: Path to SSL cert, or **None** to cancel SSL verifying
        """
        self.session_id = None
        self.auto_keepalive_sender = AsyncAutoKeepaliveSender(async_lm=self)
        self.api = AsyncSecureApiWrapper(url=root_url, ssl_cert=ssl_public_key)

    async def check_key(self, key: str) -> response.LicenseCheckResponse:
        """
        Check license key with specified Pyalic Server
        :param key: License key
        :return: `LicenseCheckResponse`
        """
        r = await self.api.check_key(key, get_fingerprint())
        processed_resp = response.process_check_key(r.status_code, r.json())
        # Start sending keepalive packets if needed
        if processed_resp.success and self.enable_auto_keepalive:
            self.auto_keepalive_sender.start()
        # Save session ID
        self.session_id = processed_resp.session_id
        return processed_resp

    async def keep_alive(self) -> response.OperationResponse:
        """
        Send keep-alive packet to license server
        (LicenseManager can do it automatically)
        :return: 'response.OperationResponse`
        """
        r = await self.api.keepalive(self.session_id)
        return response.process_keepalive(r.status_code, r.json())

    async def end_session(self) -> response.OperationResponse:
        """
        End current license session
        :return: 'response.OperationResponse`
        """
        self.auto_keepalive_sender.stop()
        r = await self.api.end_session(self.session_id)
        return response.process_end_session(r.status_code, r.json())
