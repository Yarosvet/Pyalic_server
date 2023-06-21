import requests

from .fingerprint import get_fingerprint
from .status import ACCESS_APPROVED, INITIALIZED

ATTEMPTS = 3


class LicenseManager:
    def __init__(self, root_url: str, ssl_cert: str):
        """

        :param root_url: Root URL of pyAdvancedLic Server
        :param ssl_cert:
        """
        self.url = root_url.rstrip("/\\")
        self.ssl_cert = ssl_cert
        self.session_id = None
        self._ac_signature = None
        self._ac_product = None
        self.status = INITIALIZED

    def check_key(self, key: str) -> bool:
        """
        Check license key with specified pyAdvancedLic Server
        :param key: License key
        :return: `Boolean`, whether access approved or not
        """
        with requests.Session() as session:
            attempted = 0
            while attempted < ATTEMPTS:
                try:
                    r = session.get(f"{self.url}/check_license",
                                    json={"license_key": key, "fingerprint": get_fingerprint()})
                    if r.status_code == 200:
                        j = r.json()
                        if j['success']:
                            self.session_id = j['session_id']
                            self._ac_product = j['additional_content_product']
                            self._ac_signature = j['additional_content_signature']
                            self.status = ACCESS_APPROVED
                            break
                        else:
                            self.status = j['error']
                            break

                except Exception as exc:
                    raise exc
            return self.status == ACCESS_APPROVED
