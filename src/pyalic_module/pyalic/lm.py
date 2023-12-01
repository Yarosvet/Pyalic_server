"""Synchronous LicenseManager's environment module"""
from threading import Thread
import time
import typing

from .fingerprint import get_fingerprint
from .exceptions import RequestFailed
from . import response
from .wrappers import SecureApiWrapper


class CallableBadKeepaliveEvent(typing.Protocol):  # pylint: disable=missing-class-docstring
    def __call__(self, operation_response: response.OperationResponse = None,
                 exc: Exception = None) -> typing.Any: ...


class AutoKeepaliveSender:
    """Automatic keep-alive packets sender"""

    INTERVAL = 2  # pylint: disable=duplicate-code

    alive = False
    _stop_flag = False
    _t = None
    _event = None

    def __init__(self, lm: 'LicenseManager'):
        self.lm = lm

    def start(self):
        """
        Start sending keepalive packets in a new thread (if not started)
        """
        if self.alive:
            return
        self._t = Thread(target=self._keepalive_cycle, name="LicenseAutoKeepAlive", daemon=True)
        self._t.start()

    def _keepalive_cycle(self):
        self.alive = True
        try:
            # Keepalive
            last_sent = time.time()
            resp = self.lm.keep_alive()
            while resp.success and not self._stop_flag:
                # Keep interval between requests
                time_past = time.time() - last_sent
                time.sleep(self.INTERVAL - time_past if self.INTERVAL > time_past else 0)
                # Keepalive
                last_sent = time.time()
                resp = self.lm.keep_alive()
            if not resp.success:
                self._call_event_bad_keepalive(operation_response=resp)
        except RequestFailed as exc:
            # Call event if request failed
            self._call_event_bad_keepalive(exc=exc)
        finally:
            self.alive = False

    def set_event_bad_keepalive(self, func: CallableBadKeepaliveEvent) -> None:
        """
        Set function-event will be called when keep-alive request goes wrong.

        Function must expect two arguments:

        ``operation_response: response.OperationResponse = None, exc: Exception = None``

        It gets one of two arguments:
        operation_response, if request returned wrong answer
        exc, if something caused exception while trying to send request
        """
        self._event = func

    def _call_event_bad_keepalive(self, operation_response: response.OperationResponse = None,
                                  exc: Exception = None) -> None:
        if self._event is not None:
            self._event(operation_response=operation_response, exc=exc)

    def stop(self):
        """Stop sending keepalive packets"""
        self._stop_flag = True


class LicenseManager:
    """Synchronous License Manager"""
    ENABLE_AUTO_KEEPALIVE = True

    def __init__(self, root_url: str, ssl_public_key: str | None = None):
        """
        Synchronous License Manager
        :param root_url: Root URL of pyAdvancedLic Server
        :param ssl_public_key: Path to SSL cert, or **None** to cancel SSL verifying
        """
        self.session_id = None
        self.auto_keepalive_sender = AutoKeepaliveSender(lm=self)
        self.api = SecureApiWrapper(url=root_url, ssl_cert=False if ssl_public_key is None else ssl_public_key)

    def check_key(self, key: str) -> response.LicenseCheckResponse:
        """
        Check license key with specified Pyalic Server
        :param key: License key
        :return: `response.LicenseCheckResponse`
        """
        r = self.api.check_key(key, get_fingerprint())
        processed_resp = response.process_check_key(r.status_code, r.json())
        # Save session ID
        self.session_id = processed_resp.session_id
        # Start sending keepalive packets if needed
        if processed_resp.success and self.ENABLE_AUTO_KEEPALIVE:
            self.auto_keepalive_sender.start()
        return processed_resp

    def keep_alive(self) -> response.OperationResponse:
        """
        Send keep-alive packet to license server
        (LicenseManager can do it automatically)
        :return: 'response.OperationResponse`
        """
        r = self.api.keepalive(self.session_id)
        return response.process_keepalive(r.status_code, r.json())

    def end_session(self) -> response.OperationResponse:
        """
        End current license session
        :return: 'response.OperationResponse`
        """
        self.auto_keepalive_sender.stop()
        r = self.api.end_session(self.session_id)
        return response.process_end_session(r.status_code, r.json())
