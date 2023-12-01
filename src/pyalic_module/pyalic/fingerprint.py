"""Fingerprinting module"""
import platform as pl
import uuid

_FINGERPRINT = None


def get_fingerprint() -> str:
    """
    :return: Fingerprint of this OS and machine
    """
    global _FINGERPRINT  # pylint: disable=global-statement
    if _FINGERPRINT is None:
        sb = [pl.node(), pl.architecture()[0], pl.architecture()[1], pl.machine(), pl.processor(), pl.system(),
              str(uuid.getnode())]
        _FINGERPRINT = '#'.join(sb)

    return _FINGERPRINT
