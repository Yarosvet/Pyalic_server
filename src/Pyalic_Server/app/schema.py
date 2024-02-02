"""
Pydantic schemas
"""
from typing import Any
from pydantic import BaseModel  # pylint: disable=no-name-in-module


class UnspecifiedModel(BaseModel):
    """
    Model with nullable fields;
    If field really was not specified its name will be in `UnspecifiedModel.unspecified_fields`
    """
    __slots__ = ('unspecified_fields',)

    def __init__(self, **data: Any):
        super().__init__(**data)
        unspecified = set()
        for field in self.model_fields:
            if field not in data:
                unspecified.add(field)
        object.__setattr__(self, 'unspecified_fields', unspecified)


# pylint: disable=missing-class-docstring

class ShortProduct(BaseModel):
    name: str
    sig_install_limit: int | None
    sig_sessions_limit: int | None
    sig_period: int | None


class AddProduct(ShortProduct):
    additional_content: str = ""


class UpdateProduct(UnspecifiedModel):
    id: int
    name: str = None
    sig_install_limit: int | None = None
    sig_sessions_limit: int | None = None
    sig_period: int | None = None
    additional_content: str | None = None


class GetProduct(ShortProduct):
    id: int
    additional_content: str = ""
    signatures: int


class ListedProduct(ShortProduct):
    id: int
    signatures: int


class IdField(BaseModel):
    id: int


class Successful(BaseModel):
    success: bool = True


class ListProducts(BaseModel):
    products: list[ListedProduct]
    items: int


class ShortSignature(BaseModel):
    id: int
    comment: str


class GetSignature(ShortSignature):
    product_id: int
    license_key: str
    additional_content: str
    installed: int
    activation_date: str | None


class AddSignature(BaseModel):
    product_id: int
    license_key: str
    additional_content: str = ""
    comment: str = ""
    activate: bool = False


class UpdateSignature(UnspecifiedModel):
    id: int
    comment: str = None
    license_key: str = None
    additional_content: str = None


class ProductsLimitOffset(BaseModel):
    limit: int = 100
    offset: int = 0


class SignaturesLimitOffset(BaseModel):
    product_id: int
    limit: int = 100
    offset: int = 0


class ListSignatures(BaseModel):
    signatures: list[ShortSignature]
    product_id: int
    items: int


class CheckLicense(BaseModel):
    license_key: str
    fingerprint: str


class BadLicense(BaseModel):
    success: bool = False
    error: str


class GoodLicense(BaseModel):
    success: bool = True
    session_id: str
    additional_content_signature: str
    additional_content_product: str


class SessionIdField(BaseModel):
    session_id: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserId(BaseModel):
    id: int


class User(UserId):
    username: str


class UserWithMaster(User):
    master_id: int | None


class ExpandedUser(UserWithMaster):
    permissions: str


class ListUsers(BaseModel):
    users: list[User]
    items: int


class UsersLimitOffset(BaseModel):
    limit: int = 100
    offset: int = 0


class AddUser(BaseModel):
    username: str
    password: str
    permissions: str


class UpdateUser(UnspecifiedModel):
    id: int
    username: str = None
    permissions: str = None
    password: str = None
