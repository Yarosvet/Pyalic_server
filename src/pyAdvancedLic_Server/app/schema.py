from pydantic import BaseModel


class ShortProduct(BaseModel):
    name: str
    sig_install_limit: int | None
    sig_sessions_limit: int | None
    sig_period: int | None


class AddProduct(ShortProduct):
    additional_content: str = ""


class UpdateProduct(ShortProduct):
    additional_content: str = ""
    id: int


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
    success = True


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
    additional_content: str
    comment: str
    activate: bool = False


class UpdateSignature(ShortSignature):
    license_key: str
    additional_content: str


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
    success = False
    error: str


class GoodLicense(BaseModel):
    success = True
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


class User(BaseModel):
    username: str
