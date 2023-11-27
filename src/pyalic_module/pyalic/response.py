"""Responses environment and managing responses"""
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


def process_check_key(status_code: int, content: dict) -> LicenseCheckResponse:
    """Process response for checking key"""
    if status_code == 200:
        if content['success']:
            return LicenseCheckResponse(request_code=status_code,
                                        success=True,
                                        content=content,
                                        session_id=content['session_id'],
                                        additional_content_product=content['additional_content_product'],
                                        additional_content_signature=content['additional_content_signature'])
        return LicenseCheckResponse(request_code=status_code,
                                    success=False, content=content,
                                    error=content['error'])
    if 'error' in content.keys():
        return LicenseCheckResponse(request_code=status_code,
                                    success=False, content=content,
                                    error=content['error'])
    if 'detail' in content.keys():
        return LicenseCheckResponse(request_code=status_code,
                                    success=False,
                                    content=content,
                                    error=content['detail'])
    return LicenseCheckResponse(request_code=status_code, success=False, content=content)


def process_keepalive(status_code: int, content: dict) -> OperationResponse:
    """Process response for keepalive"""
    if status_code == 200 and content['success']:
        return OperationResponse(request_code=status_code, success=True, content=content)
    if 'error' in content.keys():
        return OperationResponse(request_code=status_code,
                                 success=False,
                                 content=content,
                                 error=content['error'])
    if 'detail' in content.keys():
        return OperationResponse(request_code=status_code,
                                 success=False,
                                 content=content,
                                 error=content['detail'])
    return OperationResponse(request_code=status_code, success=False, content=content)


def process_end_session(status_code: int, content: dict) -> OperationResponse:
    """Process response for ending session"""
    if status_code == 200 and content['success']:
        return OperationResponse(request_code=status_code, success=True, content=content)
    if 'error' in content.keys():
        return LicenseCheckResponse(request_code=status_code, success=False, content=content, error=content['error'])
    if 'detail' in content.keys():
        return LicenseCheckResponse(request_code=status_code, success=False, content=content,
                                    error=content['detail'])
    return OperationResponse(request_code=status_code, success=False, content=content)
