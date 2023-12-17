# First message
# Каталог - категории товаров
from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_async_engine(os.getenv('SQLALCHEMY_URL'), echo=True)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)


class Category(Base):
    __tablename__ = 'categories'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    products = relationship('Product', back_populates='category')


class Brand(Base):
    __tablename__ = 'brands'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    products = relationship('Product', back_populates='brand')


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    photo: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    price: Mapped[int] = mapped_column()
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id'))
    brand_id: Mapped[int] = mapped_column(ForeignKey('brands.id'))

    category = relationship('Category', back_populates='products')
    brand = relationship('Brand', back_populates='products')
    size = relationship('Size', back_populates='products')


class Size(Base):
    __tablename__ = 'sizes'
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('products.id'))
    size_m: Mapped[int] = mapped_column()
    size_l: Mapped[int] = mapped_column()
    size_xl: Mapped[int] = mapped_column()
    size_xxl: Mapped[int] = mapped_column()
    size_3xl: Mapped[int] = mapped_column()

    products = relationship('Product', back_populates='size')


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
