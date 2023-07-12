import requests
from threading import Thread
import time

from .fingerprint import get_fingerprint
from .status import ACCESS_APPROVED, INITIALIZED, SESSION_ENDED

ATTEMPTS = 3


class BadResponse(Exception):
    def __init__(self, code, *args):
        super().__init__(*args)
        self.code = code

    def __repr__(self):
        return f"BadResponse {self.code}"


class LicenseManager:
    def __init__(self, root_url: str, ssl_public_key: str | None = None):
        """
        Class for managing license
        :param root_url: Root URL of pyAdvancedLic Server
        :param ssl_public_key: Path to SSL cert, or **None** to cancel SSL verifying
        """
        self.url = root_url.rstrip("/\\")
        self.ssl_pkey = False if ssl_public_key is None else ssl_public_key
        self.session_id = None
        self._ac_signature = None
        self._ac_product = None
        self.status = INITIALIZED
        self.ka_thread = None
        self.keepalive_interval = 2

    def check_key(self, key: str) -> bool:
        """
        Check license key with specified pyAdvancedLic Server
        :param key: License key
        :return: `Boolean`, whether access approved or not
        """
        with requests.Session() as session:
            attempted = 0
            while attempted < ATTEMPTS:
                attempted += 1
                try:
                    r = session.get(f"{self.url}/check_license", verify=self.ssl_pkey,
                                    json={"license_key": key, "fingerprint": get_fingerprint()})
                    j = r.json()
                    if r.status_code == 200:
                        if j['success']:
                            self.session_id = j['session_id']
                            self._ac_product = j['additional_content_product']
                            self._ac_signature = j['additional_content_signature']
                            self.status = ACCESS_APPROVED
                            self.ka_thread = Thread(target=self._ka_cycle, name="LicenseKeepAlive", daemon=True)
                            self.ka_thread.start()
                            break
                        else:
                            self.status = j['error']
                            break
                    else:
                        if 'error' in j.keys():
                            self.status = j['error']
                            break
                        elif 'detail' in j.keys():
                            self.status = j['detail']
                            break
                        else:
                            raise BadResponse(r.status_code)

                except Exception as exc:
                    raise exc
            return self.status == ACCESS_APPROVED

    def event_bad_keepalive(self, status_code: int, msg: str | None = None) -> None:
        """
        Event will be called when keep-alive request goes wrong.
        Feel free to override this method, for example to end session on this event
        """
        pass

    def keep_alive(self) -> None:
        with requests.Session() as session:
            attempted = 0
            while attempted < ATTEMPTS:
                attempted += 1
                try:
                    r = session.post(f"{self.url}/keepalive", json={"session_id": self.session_id},
                                     verify=self.ssl_pkey)
                    j = r.json()
                    if r.status_code == 200 and j['success']:
                        break
                    else:
                        if 'error' in j.keys():
                            self.event_bad_keepalive(r.status_code, j['error'])
                            break
                        elif 'detail' in j.keys():
                            self.event_bad_keepalive(r.status_code, j['detail'])
                            break
                        else:
                            raise BadResponse(r.status_code)

                except Exception as exc:
                    if isinstance(exc, BadResponse) and attempted < ATTEMPTS:
                        continue
                    self.event_bad_keepalive(r.status_code, str(exc))

    def end_session(self) -> bool:
        """
        End current license session
        :return: Boolean, whether request successful or not
        """
        with requests.Session() as session:
            attempted = 0
            while attempted < ATTEMPTS:
                attempted += 1
                try:
                    r = session.post(f"{self.url}/end_session", json={"session_id": self.session_id},
                                     verify=self.ssl_pkey)
                    j = r.json()
                    if r.status_code == 200 and j['success']:
                        self.status = SESSION_ENDED
                        return True
                    else:
                        raise BadResponse(r.status_code)

                except Exception as exc:
                    if isinstance(exc, BadResponse) and attempted < ATTEMPTS:
                        continue
                    return False

    def _ka_cycle(self):
        while self.status == ACCESS_APPROVED:
            self.keep_alive()
            time.sleep(self.keepalive_interval)
