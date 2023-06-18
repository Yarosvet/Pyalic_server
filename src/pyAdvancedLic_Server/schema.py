from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    name: str
    sig_install_limit: int | None
    sig_sessions_limit: int | None
    sig_period: int | None
    additional_content: str = ""

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
    items: int


class Signature(BaseModel):
    success: bool = True
    id: int
    product_id: int
    license_key: str
    additional_content: str
    comment: str
    installed: int
    activation_date: str | None


class ShortSignature(BaseModel):
    id: int
    comment: str


class ProductsLimitOffset(BaseModel):
    limit: int = 100
    offset: int = 0


class SignaturesLimitOffset(BaseModel):
    product_id: int
    limit: int = 100
    offset: int = 0


class ListSignatures(BaseModel):
    success: bool = True
    signatures: list[ShortSignature]
    product_id: int
    items: int
