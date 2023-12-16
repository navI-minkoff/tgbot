from app.database.models import User, Category, Product, Brand, async_session
from sqlalchemy import select
from sqlalchemy import insert
from aiogram.fsm.context import FSMContext


async def get_categories():
    async with async_session() as session:
        result = await session.scalars(select(Category))

        return result


async def get_products(category_id):
    async with async_session() as session:
        result = await session.scalars(select(Product).where(Product.category_id == category_id))

        return result


async def get_product(product_id) -> Product:
    async with async_session() as session:
        result = await session.scalar(select(Product).where(Product.id == product_id))

        return result


async def add_product(state: FSMContext):
    data = await state.get_data()
    category_id = select(Category).where(Category.name == data['type'])
    brand_id = select(Brand).where(Brand.name == data['brand'])
    product = Product(name=data['name'], photo=data['photo'], description=data['desc'], price=data['price'],
                      category_id=data['type'], brand_id=1)
    async with async_session() as session:
        session.add(product)
        await session.commit()
