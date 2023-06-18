from sqlalchemy import Column, BigInteger, Integer, Interval, Text, DateTime, orm, ForeignKey

from . import SqlAlchemyBase


class Signature(SqlAlchemyBase):
    __tablename__ = "signatures"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    license_key = Column(Text, nullable=False)
    additional_content = Column(Text, default='', nullable=False)
    comment = Column(Text, default="", nullable=False)
    installed = Column(BigInteger, default=0, nullable=False)
    activation_date = Column(DateTime, default=None)

    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    product = orm.relationship("Product")


class Product(SqlAlchemyBase):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    sig_install_limit = Column(Integer, default=None)  # Limit installs per signature
    sig_sessions_limit = Column(Integer, default=None)  # Limit sessions per signature
    sig_period = Column(Interval, default=None)  # License period per signature
    additional_content = Column(Text, default='', nullable=False)

    signatures = orm.relationship("Signature", back_populates="product")
