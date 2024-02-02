"""SQLAlchemy ORM models placed here"""
from sqlalchemy import Column, BigInteger, Integer, Interval, Text, DateTime, orm, ForeignKey, Table

from . import SqlAlchemyBase
from ..access.permissions import DEFAULT_PERMISSIONS, VerifiablePermissions, Permissions

user_product_table = Table(
    "user_product",
    SqlAlchemyBase.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)


class Signature(SqlAlchemyBase):
    """Signature Model for SQLAlchemy"""
    __tablename__ = "signatures"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    license_key = Column(Text, nullable=False, unique=True)
    additional_content = Column(Text, default='', nullable=False)
    comment = Column(Text, default="", nullable=False)
    activation_date = Column(DateTime, default=None)

    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    product = orm.relationship("Product")

    installations = orm.relationship("Installation", back_populates="signature")


class Product(SqlAlchemyBase):
    """Product Model for SQLAlchemy"""
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    sig_install_limit = Column(Integer, default=None)  # Limit installs per signature
    sig_sessions_limit = Column(Integer, default=None)  # Limit sessions per signature
    sig_period = Column(Interval, default=None)  # License period per signature
    additional_content = Column(Text, default='', nullable=False)

    signatures = orm.relationship("Signature", back_populates="product")

    owners = orm.relationship('User', secondary=user_product_table, back_populates="owned_products")


class Installation(SqlAlchemyBase):
    """Installation Model for SQLAlchemy"""
    __tablename__ = "installations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fingerprint = Column(Text, nullable=False)

    signature_id = Column(BigInteger, ForeignKey("signatures.id"), nullable=False)
    signature = orm.relationship("Signature")


class User(SqlAlchemyBase):
    """User Model for SQLAlchemy"""
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False)
    hashed_password = Column(Text, nullable=False)
    permissions = Column(Text, default=DEFAULT_PERMISSIONS, nullable=False)

    owned_products = orm.relationship('Product', secondary=user_product_table, back_populates="owners")

    master_id = Column(BigInteger, ForeignKey('users.id'))
    master = orm.relationship('User', backref='slaves', remote_side='User.id', lazy='joined')

    def get_permissions(self) -> Permissions:
        """
        :return: Permissions object interpretation
        """
        return Permissions(self.permissions)

    def get_verifiable_permissions(self) -> VerifiablePermissions:
        """
        :return: VerifiablePermissions object interpretation
        """
        return VerifiablePermissions(self)
