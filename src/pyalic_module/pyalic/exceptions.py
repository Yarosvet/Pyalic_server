"""Exceptions of Pylic module"""


class BadResponse(Exception):
    """Got unexpected response"""
    def __init__(self, code, *args):
        super().__init__(*args)
        self.code = code

    def __repr__(self):
        return f"BadResponse {self.code}"
