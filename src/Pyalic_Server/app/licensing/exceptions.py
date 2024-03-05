"""
Errors of verifying license key
"""
from fastapi.exceptions import HTTPException


class InvalidKeyException(HTTPException):
    """Invalid license key"""

    def __init__(self):
        super().__init__(status_code=400, detail="Invalid license key")


class LicenseExpiredException(HTTPException):
    """License expired"""

    def __init__(self):
        super().__init__(status_code=400, detail="License expired")


class SessionsLimitException(HTTPException):
    """Sessions limit exceeded"""

    def __init__(self):
        super().__init__(status_code=400, detail="Sessions limit exceeded")


class InstallationsLimitException(HTTPException):
    """Installations limit exceeded"""

    def __init__(self):
        super().__init__(status_code=400, detail="Installations limit exceeded")
