from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    name: str
    sig_install_limit: int | None
    sig_sessions_limit: int | None
    sig_period: int | None
    additional_content: str

    id: Optional[int]
    signatures: Optional[int]
    success: Optional[bool]


class IdField(BaseModel):
    id: int


class Unsuccessful(BaseModel):
    success = False,
    error: str | None


class Successful(BaseModel):
    success = True


class ListProducts(BaseModel):
    success: bool = True
    products: list[Product]


class Signature(BaseModel):
    license_key: str
    additional_content: str
    comment: str

    installed: Optional[int]
    activate: Optional[bool]
    id: Optional[int]
