from pydantic import BaseModel, root_validator


class UnspecifiedModel(BaseModel):
    _unspecified = []

    @root_validator(pre=True)
    def mark_as_unspecified(cls, values: dict):
        for field in cls.__fields__:
            print(field)
            if field not in values.keys():
                cls._unspecified.append(field)
        return values

    @property
    def unspecified_fields(self) -> list[str]:
        return self._unspecified


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
    success = False
    error: str


class GoodLicense(BaseModel):
    success = True
    session_id: str
    additional_content_signature: str
    additional_content_product: str


class SessionIdField(BaseModel):
    session_id: str
