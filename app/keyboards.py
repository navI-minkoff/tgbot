from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from app.database.requests import get_categories
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Каталог')],
    [KeyboardButton(text='Контакты')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт ниже')


async def categories():
    categories_kb = InlineKeyboardBuilder()
    categories = await get_categories()

    for category in categories:
        categories_kb.add(InlineKeyboardButton(text=category.name, callback_data=f'category_{category.id}'))

    return categories_kb.adjust(2).as_markup()