"""Synchronous LicenseManager's environment module"""
from threading import Thread
import time
import requests

from .fingerprint import get_fingerprint
from .exceptions import RequestFailed
from .response import LicenseCheckResponse, OperationResponse

ATTEMPTS = 3


class AutoKeepaliveSender:
    """Automatic keep-alive packets sender"""

    INTERVAL = 2

    alive = False
    _stop_flag = False
    _t = None

    def __init__(self, lm: 'LicenseManager'):
        self.lm = lm

    def start(self):
        """
        Start sending keepalive packets in a new thread.
        If already started, it will stop existing thread and start a new one
        """
        if self.alive:
            self.stop()
            while self.alive:
                time.sleep(0.01)
        self._t = Thread(target=self._ka_cycle, name="LicenseAutoKeepAlive", daemon=True)
        self._t.start()

    def _ka_cycle(self):
        self.alive = True
        try:
            last_sent = time.time()
            resp = self.lm.keep_alive()
            while resp.success:
                if self._stop_flag:
                    break
                time_past = time.time() - last_sent
                time.sleep(self.INTERVAL - time_past if self.INTERVAL > time_past else 0)
                resp = self.lm.keep_alive()
            if not resp.success:
                self.event_bad_keepalive(operation_response=resp)
        except RequestFailed as exc:
            self.event_bad_keepalive(exc=exc)
        finally:
            self.alive = False

    def event_bad_keepalive(self, operation_response: OperationResponse = None, exc: Exception = None) -> None:
        """
        Event will be called when keep-alive request goes wrong.
        Feel free to override this method, for example to end session on this event

        It gets one of two arguments:
        operation_response, if request returned wrong answer
        exc, if something caused exception while trying to send request
        """

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
        self.url = root_url.rstrip("/\\")
        self.ssl_pkey = False if ssl_public_key is None else ssl_public_key
        self.session_id = None
        self.auto_keepalive_sender = AutoKeepaliveSender(lm=self)

    def check_key(self, key: str) -> LicenseCheckResponse:
        """
        Check license key with specified pyAdvancedLic Server
        :param key: License key
        :return: `LicenseCheckResponse`
        """
        attempted = 0
        while True:
            attempted += 1
            try:
                with requests.Session() as session:
                    r = session.get(f"{self.url}/check_license", verify=self.ssl_pkey,
                                    json={"license_key": key, "fingerprint": get_fingerprint()})
                    j = r.json()
                break
            except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as exc:
                if attempted < ATTEMPTS:
                    continue
                raise RequestFailed from exc
        if r.status_code == 200:
            if j['success']:
                if self.ENABLE_AUTO_KEEPALIVE:
                    self.auto_keepalive_sender.start()
                self.session_id = j['session_id']
                return LicenseCheckResponse(request_code=r.status_code,
                                            success=True,
                                            content=j,
                                            session_id=j['session_id'],
                                            additional_content_product=j['additional_content_product'],
                                            additional_content_signature=j['additional_content_signature'])
            return LicenseCheckResponse(request_code=r.status_code, success=False, content=j, error=j['error'])
        if 'error' in j.keys():
            return LicenseCheckResponse(request_code=r.status_code, success=False, content=j, error=j['error'])
        if 'detail' in j.keys():
            return LicenseCheckResponse(request_code=r.status_code, success=False, content=j, error=j['detail'])
        return LicenseCheckResponse(request_code=r.status_code, success=False, content=j)

    def keep_alive(self) -> OperationResponse:
        """
        Send keep-alive packet to license server
        (LicenseManager can do it automatically)
        :return: 'OperationResponse`
        """
        with requests.Session() as session:
            attempted = 0
            while True:
                attempted += 1
                try:
                    r = session.post(f"{self.url}/keepalive", json={"session_id": self.session_id},
                                     verify=self.ssl_pkey)
                    j = r.json()
                except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as exc:
                    if attempted < ATTEMPTS:
                        continue
                    raise RequestFailed from exc
        if r.status_code == 200 and j['success']:
            return OperationResponse(request_code=r.status_code, success=True, content=j)
        if 'error' in j.keys():
            resp = OperationResponse(request_code=r.status_code,
                                     success=False,
                                     content=j,
                                     error=j['error'])
            return resp
        if 'detail' in j.keys():
            resp = OperationResponse(request_code=r.status_code,
                                     success=False,
                                     content=j,
                                     error=j['detail'])
            return resp
        return OperationResponse(request_code=r.status_code, success=False, content=j)

    def end_session(self) -> OperationResponse:
        """
        End current license session
        :return: Boolean, whether request successful or not
        """
        self.auto_keepalive_sender.stop()
        with requests.Session() as session:
            attempted = 0
            while True:
                attempted += 1
                try:
                    r = session.post(f"{self.url}/end_session", json={"session_id": self.session_id},
                                     verify=self.ssl_pkey)
                    j = r.json()
                    break
                except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as exc:
                    if attempted < ATTEMPTS:
                        continue
                    raise RequestFailed from exc
        if r.status_code == 200 and j['success']:
            return OperationResponse(request_code=r.status_code, success=True, content=j)
        if 'error' in j.keys():
            return LicenseCheckResponse(request_code=r.status_code, success=False, content=j, error=j['error'])
        if 'detail' in j.keys():
            return LicenseCheckResponse(request_code=r.status_code, success=False, content=j, error=j['detail'])
        return OperationResponse(request_code=r.status_code, success=False, content=j)
