import array
import csv
import json
from dataclasses import asdict
from sqlite3 import IntegrityError
from app.database.models import User, Category, Product, Brand, async_session, Cart, Custom, Departure, engine
from sqlalchemy import select, update, insert, and_, delete
from aiogram.fsm.context import FSMContext
import pandas as pd
from openpyxl import Workbook


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

        return new_custom_id


def subtract_json(json1, json2):
    result = json1.copy()
    for key, value in json2.items():
        result[key] = max(0, result.get(key, 0) - value)
    return result


async def clear_cart_and_update_product(user_id):
    async with async_session() as session:
        products_in_cart = await get_products_in_cart_user(user_id)
        for product_in_cart in products_in_cart:
            new_product = await get_product(product_in_cart.product_id)
            new_sizes = subtract_json(new_product.sizes, product_in_cart.size)
            sizes = new_sizes
            await session.execute(update(Product).where(Product.id == new_product.id).values(sizes=sizes))
            await session.commit()

        await session.execute(delete(Cart).where(Cart.user_id == user_id))
        await session.commit()


async def export_database_to_csv_and_xlsx(csv_filename, xlsx_filename, file_format):
    async with async_session() as session:

        users = await session.execute(select(User))
        users_data = [dict(user.__dict__) for user in users.scalars().all()]
        for user_data in users_data:
            del user_data[next(iter(user_data))]
        users_df = pd.DataFrame(users_data)

        categories = await session.execute(select(Category))
        categories_data = [dict(category.__dict__) for category in categories.scalars().all()]
        for category_data in categories_data:
            del category_data[next(iter(category_data))]
        categories_df = pd.DataFrame(categories_data)

        brand = await session.execute(select(Brand))
        brands_data = [dict(brand.__dict__) for brand in brand.scalars().all()]
        for brand_data in brands_data:
            del brand_data[next(iter(brand_data))]
        brands_df = pd.DataFrame(brands_data)

        product = await session.execute(select(Product))
        products_data = [dict(product.__dict__) for product in product.scalars().all()]
        for product_data in products_data:
            del product_data[next(iter(product_data))]
        products_df = pd.DataFrame(products_data)

        cart = await session.execute(select(Cart))
        carts_data = [dict(cart.__dict__) for cart in cart.scalars().all()]
        for cart_data in carts_data:
            del cart_data[next(iter(cart_data))]
        cart_df = pd.DataFrame(carts_data)

        custom = await session.execute(select(Custom))
        customs_data = [dict(custom.__dict__) for custom in custom.scalars().all()]
        for custom_data in customs_data:
            del custom_data[next(iter(custom_data))]
        custom_df = pd.DataFrame(customs_data)

        departure = await session.execute(select(Departure))
        departures_data = [dict(departure.__dict__) for departure in departure.scalars().all()]
        for departure_data in departures_data:
            del departure_data[next(iter(departure_data))]
        departure_df = pd.DataFrame(departures_data)

    if file_format == 'csv':
        users_df.to_csv(csv_filename, index=False)
        categories_df.to_csv(csv_filename, mode='a', index=False)
        brands_df.to_csv(csv_filename, mode='a', index=False)
        products_df.to_csv(csv_filename, mode='a', index=False)
        cart_df.to_csv(csv_filename, mode='a', index=False)
        custom_df.to_csv(csv_filename, mode='a', index=False)
        departure_df.to_csv(csv_filename, mode='a', index=False)

    elif file_format == 'xlsx':
        with pd.ExcelWriter(xlsx_filename, engine='openpyxl') as writer:
            users_df.to_excel(writer, sheet_name='users', index=False)
            categories_df.to_excel(writer, sheet_name='categories', index=False)
            brands_df.to_excel(writer, sheet_name='brands', index=False)
            products_df.to_excel(writer, sheet_name='products', index=False)
            cart_df.to_excel(writer, sheet_name='cart', index=False)
            custom_df.to_excel(writer, sheet_name='custom', index=False)
            departure_df.to_excel(writer, sheet_name='departure', index=False)
