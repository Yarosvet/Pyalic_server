"""Responses environment and managing responses"""
from dataclasses import dataclass
from collections import ChainMap


@dataclass
class OperationResponse:
    """Response from server for some operation"""
    request_code: int
    success: bool
    content: dict
    error: str = None

    @classmethod
    def _get_annotations(cls):
        """Get annotations from all parent classes including current class"""
        return ChainMap(*(c.__annotations__ for c in cls.__mro__ if '__annotations__' in c.__dict__))

    def __post_init__(self):
        for (name, field_type) in self.__class__._get_annotations().items():  # pylint: disable=protected-access
            if not isinstance(getattr(self, name), field_type) and getattr(self, name) is not None:
                setattr(self, name, field_type(getattr(self, name)))


@dataclass
class LicenseCheckResponse(OperationResponse):
    """Response from server for checking license"""
    session_id: str = None
    additional_content_signature: str = ""
    additional_content_product: str = ""


def process_check_key(status_code: int, content: dict) -> LicenseCheckResponse:
    """Process response for checking key"""
    if status_code == 200 and 'success' in content and content['success']:
        return LicenseCheckResponse(request_code=status_code,
                                    success=True,
                                    content=content,
                                    session_id=content['session_id'],
                                    additional_content_product=content['additional_content_product'],
                                    additional_content_signature=content['additional_content_signature'])
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
    if status_code == 200 and 'success' in content and content['success']:
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
    if status_code == 200 and 'success' in content and content['success']:
        return OperationResponse(request_code=status_code, success=True, content=content)
    if 'error' in content.keys():
        return LicenseCheckResponse(request_code=status_code, success=False, content=content, error=content['error'])
    if 'detail' in content.keys():
        return LicenseCheckResponse(request_code=status_code, success=False, content=content,
                                    error=content['detail'])
    return OperationResponse(request_code=status_code, success=False, content=content)
