from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from app.database.requests import get_categories, get_products, get_brands
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.admin import NewOrder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Каталог')],
    [KeyboardButton(text='Корзина')],
    [KeyboardButton(text='Контакты')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже')

main_admin = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Каталог')],
    [KeyboardButton(text='Корзина')],
    [KeyboardButton(text='Админ-панель')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже')

admin_panel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Добавить товар')],
    [KeyboardButton(text='Удалить товар')],
    [KeyboardButton(text='Сделать рассылку')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже')

cancel = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отмена')]

], resize_keyboard=True)


async def categories(is_admin: bool):
    categories_kb = InlineKeyboardBuilder()
    _categories = await get_categories()
    text = 'category_'
    if is_admin:
        text = ''
    for category in _categories:
        categories_kb.add(InlineKeyboardButton(text=category.name, callback_data=text + f'{category.id}'))

    return categories_kb.adjust(2).as_markup()


async def brands():
    brands_kb = InlineKeyboardBuilder()
    _brands = await get_brands()
    for brand in _brands:
        brands_kb.add(InlineKeyboardButton(text=brand.name, callback_data=f'{brand.id}'))

    return brands_kb.adjust(2).as_markup()

async def products(category_id):
    product_kb = InlineKeyboardBuilder()
    products_ = await get_products(category_id)

    for product in products_:
        product_kb.add(InlineKeyboardButton(text=product.name, callback_data=f'product_{product.id}'))

    return product_kb.adjust(2).as_markup()
