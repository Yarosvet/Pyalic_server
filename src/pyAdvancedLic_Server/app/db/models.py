from sqlalchemy import Column, BigInteger, Integer, Interval, Text, DateTime, orm, ForeignKey

from . import SqlAlchemyBase
from ..access.permissions import DEFAULT_PERMISSIONS


class Signature(SqlAlchemyBase):
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
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    sig_install_limit = Column(Integer, default=None)  # Limit installs per signature
    sig_sessions_limit = Column(Integer, default=None)  # Limit sessions per signature
    sig_period = Column(Interval, default=None)  # License period per signature
    additional_content = Column(Text, default='', nullable=False)

    signatures = orm.relationship("Signature", back_populates="product")


class Installation(SqlAlchemyBase):
    __tablename__ = "installations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    fingerprint = Column(Text, nullable=False)

    signature_id = Column(BigInteger, ForeignKey("signatures.id"), nullable=False)
    signature = orm.relationship("Signature")


class User(SqlAlchemyBase):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False)
    hashed_password = Column(Text, nullable=False)
    permissions = Column(Text, default=DEFAULT_PERMISSIONS, nullable=False)
