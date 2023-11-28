"""Tests for Pylic module"""
import random
import string


def rand_str(length: int) -> str:
    """
    Generate random string of letters and digits
    :param length: Required length of string
    :return:
    """
    return "".join([random.choice(string.ascii_letters + string.digits) for _ in range(length)])
