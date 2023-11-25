"""Fingerprinting module"""
import platform as pl
import uuid


def get_fingerprint() -> str:
    """
    :return: Fingerprint of this OS and machine
    """
    sb = [pl.node(), pl.architecture()[0], pl.architecture()[1], pl.machine(), pl.processor(), pl.system(),
          str(uuid.getnode())]
    text = '#'.join(sb)
    return text
