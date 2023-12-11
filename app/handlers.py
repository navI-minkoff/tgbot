import os

from aiogram import Router, F, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
import app.keyboards as kb
from app.database.requests import get_product

router = Router()
dp = Dispatcher


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f'{message.from_user.first_name}, добро пожаловать!', reply_markup=kb.main)

@router.message(Command('admin'))
async def catalog(message: Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Вы авторизовались как администратор', reply_markup=kb.main_admin)
    else:
        await message.answer(f'Вы не являетесь администратором')

@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выберете вариант из каталога', reply_markup=await kb.categories())


@router.message(F.text == 'Корзина')
async def cart(message: Message):
    await message.answer('Ваша корзина')


@router.message(F.text == 'Контакты')
async def contacts(message: Message):
    await message.answer('Номер телефона')


@router.message(F.text == 'Админ-панель')
async def contacts(message: Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Вы вошли в админ-панель', reply_markup=kb.admin_panel)
    else:
        await message.answer(f'Вы не являетесь администратором')



@router.callback_query(F.data.startswith('category_'))
async def category_selected(callback: CallbackQuery):
    category_id = callback.data.split('_')[1]
    await callback.message.answer(f'Товары по выбранной категории:', reply_markup=await kb.products(category_id))
    await callback.answer('')


@router.callback_query(F.data.startswith('product_'))
async def product_selected(callback: CallbackQuery):
    product_id = callback.data.split('_')[1]
    product = await get_product(product_id=product_id)
    await callback.message.answer(f'<b>{product.name}</b>\n\n{product.description}\n\nЦена: {product.price} руб')
    await callback.answer(f'Вы выбрали {product.name}')


@router.message()
async def answer(message: Message):
    await message.reply('Я тебя не понимаю(')
