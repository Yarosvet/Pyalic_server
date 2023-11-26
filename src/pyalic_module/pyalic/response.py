"""LicenseCheckResponse environment"""
from dataclasses import dataclass


@dataclass
class OperationResponse:
    """Response from server for some operation"""
    request_code: int
    success: bool
    content: dict
    error: str = None


@dataclass
class LicenseCheckResponse(OperationResponse):
    """Response from server for checking license"""
    session_id: str = None
    additional_content_signature: str = ""
    additional_content_product: str = ""
