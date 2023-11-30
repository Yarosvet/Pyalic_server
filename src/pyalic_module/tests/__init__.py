"""Tests for Pylic module"""
import random
import string
from os import path

_DIR_PATH = path.split(path.abspath(__file__))[:-1]

SERVER_PORT = 8080
CERT_FILE = path.join(*_DIR_PATH, "ssl/", "cert.crt")
KEY_FILE = path.join(*_DIR_PATH, "ssl/", "key.key")


def rand_str(length: int) -> str:
    """
    Generate random string of letters and digits
    :param length: Required length of string
    :return:
    """
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])
