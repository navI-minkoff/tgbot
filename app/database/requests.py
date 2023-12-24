import array
import json
from sqlite3 import IntegrityError

from app.database.models import User, Category, Product, Brand, async_session, Cart, Custom, Departure
from sqlalchemy import select, update, insert, and_
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


async def check_product(state: FSMContext):
    data = await state.get_data()

    async with async_session() as session:
        result = await session.scalar(select(Product).where(Product.name == data['name']))

        return bool(result)


async def get_cart_by_user_and_product(user_id, product_id):
    async with async_session() as session:
        statement = select(Cart).where(and_(Cart.user_id == user_id, Cart.product_id == product_id))
        result = await session.execute(statement)
        return result.scalar_one_or_none()


async def add_product_in_cart(user_id, product_id, product_size):
    async with async_session() as session:
        existing_cart = await get_cart_by_user_and_product(user_id, product_id)
        if existing_cart is not None:
            cart_data = existing_cart.size
            if product_size in cart_data:
                cart_data[product_size] += 1
            else:
                cart_data[product_size] = 1
            existing_cart.size = cart_data
            await session.execute(update(Cart).where(Cart.id == existing_cart.id).values(size=cart_data))
        else:
            json_size = {product_size: 1}
            new_cart = Cart(user_id=user_id, product_id=product_id, size=json_size)
            session.add(new_cart)
        await session.commit()


async def delete_product(product_id):
    async with async_session() as session:
        product = await session.execute(select(Product).where(Product.id == product_id))
        product = product.scalar_one_or_none()

        if product is not None:
            await delete_cart_items_by_product_id(product_id)

            await session.delete(product)
            await session.commit()


async def delete_cart_items_by_product_id(product_id):
    async with async_session() as session:
        cart_items = await session.execute(select(Cart).where(Cart.product_id == product_id))
        cart_items = cart_items.scalars().all()

        for cart_item in cart_items:
            await session.delete(cart_item)

        await session.commit()


async def delete_product_in_cart(product_id, user_id):
    async with async_session() as session:
        result = await session.execute(select(Cart).where(and_(Cart.product_id == product_id, Cart.user_id == user_id)))
        product_in_cart = result.scalar_one_or_none()

        if product_in_cart is not None:
            await session.delete(product_in_cart)
            await session.commit()


async def get_products_in_cart_user(user_id):
    async with async_session() as session:
        result = await session.execute(select(Cart).where(Cart.user_id == user_id))
        products_in_cart = result.scalars().all()

    return products_in_cart


async def add_user_to_db(tg_id: int) -> bool:
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
                await session.execute(stmt)
            return False
        return True


def count_values_in_json(json_obj) -> int:
    try:
        if isinstance(json_obj, dict):
            return sum(json_obj.values())
        return 0
    except Exception as e:
        raise ValueError(f"Error processing JSON: {str(e)}")


def get_sizes_str(json_str) -> str:
    try:
        if isinstance(json_str, dict):
            data = json_str
        else:
            data = json.loads(json_str)

        if isinstance(data, dict):
            formatted_counts = [f"{key} : {value}" for key, value in data.items()]
            return ', '.join(formatted_counts)
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


def is_numeric(input_str):
    try:
        int_value = int(input_str)
        return str(int_value) == input_str
    except ValueError:
        return False


async def add_custom_and_departures(user_id, price, track_id, product_ids):
    async with async_session() as session:
        new_custom = Custom(user_id=user_id, price=price, track_id=track_id)
        session.add(new_custom)
        await session.commit()

        result = await session.execute(
            select(Custom).where(Custom.user_id == user_id).order_by(Custom.id.desc()).limit(1))
        new_custom = result.scalar_one()
        new_custom_id = new_custom.id

        for product_id in product_ids:
            new_departure = Departure(custom_id=new_custom_id, product_id=product_id)
            session.add(new_departure)

        await session.commit()
