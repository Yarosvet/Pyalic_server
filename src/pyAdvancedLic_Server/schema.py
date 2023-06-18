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


class Unsuccessful(BaseModel):
    success = False,
    error: str | None


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
