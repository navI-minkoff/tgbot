from sqlite3 import IntegrityError

from app.database.models import User, Category, Product, Brand, async_session
from sqlalchemy import select
from sqlalchemy import insert
from aiogram.fsm.context import FSMContext


async def get_categories():
    async with async_session() as session:
        result = await session.scalars(select(Category))

        return result


async def get_brands():
    async with async_session() as session:
        result = await session.scalars(select(Brand))

        return result


async def get_products(category_id):
    async with async_session() as session:
        result = await session.scalars(select(Product).where(Product.category_id == category_id))

        return result


async def get_product(product_id) -> Product:
    async with async_session() as session:
        result = await session.scalar(select(Product).where(Product.id == product_id))

        return result


async def get_brand(brand_id) -> Brand:
    async with async_session() as session:
        result = await session.scalar(select(Brand).where(Brand.id == brand_id))

        return result


async def add_product(state: FSMContext):
    data = await state.get_data()
    product = Product(name=data['name'], photo=data['photo'], description=data['desc'], price=data['price'],
                      category_id=data['type'], brand_id=data['brand'], sizes=data['sizes'])
    async with async_session() as session:
        session.add(product)
        await session.commit()


async def delete_product(product_id):
    async with async_session() as session:
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if product is not None:
            await session.delete(product)
            await session.commit()


async def add_user_to_db(tg_id: int):
    async with async_session() as session:
        stmt = select(User).filter(User.tg_id == tg_id)
        existing_user = await session.execute(stmt)

        if (result := existing_user.scalar()) is None:
            new_user = User(tg_id=tg_id)
            session.add(new_user)

            try:
                await session.commit()
                await session.refresh(new_user)
            except IntegrityError:
                await session.rollback()
                stmt = select(User).filter(User.tg_id == tg_id)
                existing_user = await session.execute(stmt)


