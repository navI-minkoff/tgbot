import os

from aiogram import Router, F, Dispatcher, types, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
import app.keyboards as kb
from app.database.requests import get_product, add_product, get_brand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

bot = Bot(token=os.getenv('TOKEN'), parse_mode='HTML')

memory_storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=memory_storage)


class NewOrder(StatesGroup):
    type = State()
    name = State()
    brand = State()
    photo = State()
    desc = State()
    price = State()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f'{message.from_user.first_name}, добро пожаловать!', reply_markup=kb.main)


@router.message(Command('admin'))
async def admin(message: Message):
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        await message.answer('Вы авторизовались как администратор', reply_markup=kb.main_admin)
    else:
        await message.answer(f'Вы не являетесь администратором')


@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выберете вариант из каталога', reply_markup=await kb.categories(False))


@router.message(F.text == 'Корзина')
async def cart(message: Message):
    await message.answer('Ваша корзина')


@router.message(F.text == 'Контакты')
async def contacts(message: Message):
    await message.answer('Номер телефона')


@router.message(F.text == 'Админ-панель')
async def admin_panel(message: Message):
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
    brand = await get_brand(product.brand_id)
    await bot.send_photo(callback.from_user.id, product.photo,
                         caption=f'<b>{product.name}</b>\n\nБренд:<b>{brand.name}</b>\n\n{product.description}\n\nЦена: {product.price} руб')
    await callback.answer(f'Вы выбрали {product.name}')


@router.message(StateFilter(None), F.text == 'Добавить товар')
async def add_item(message: types.Message, state: FSMContext):
    await state.set_state(NewOrder.type)
    await message.answer('Выбери тип', reply_markup=await kb.categories(True))


@router.callback_query(StateFilter(NewOrder.type))
async def add_item_type(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(type=call.data)
    await call.message.answer(f'Напишите название товара', reply_markup=kb.cancel)
    await state.set_state(NewOrder.name)


@router.message(StateFilter(NewOrder.name))
async def add_item_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f'Добавьте бренд', reply_markup=await kb.brands())
    await state.set_state(NewOrder.brand)


@router.callback_query(StateFilter(NewOrder.brand))
async def add_item_brand(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(brand=call.data)
    await call.message.answer(f'Добавьте фото', reply_markup=kb.cancel)
    await state.set_state(NewOrder.photo)


# @router.message(StateFilter(NewOrder.brand))
# async def add_item_brand(message: types.Message, state: FSMContext):
#     await state.update_data(brand=message.text)
#     await message.answer(f'Добавьте фото')
#     await state.set_state(NewOrder.photo)


@router.message(lambda message: not message.photo, StateFilter(NewOrder.photo))
async def add_item_photo_check(message: types.Message):
    await message.answer('Это не фотография')


@router.message(lambda message: message.photo, StateFilter(NewOrder.photo))
async def add_item_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[0].file_id)
    await message.answer('Добавьте описание товара')
    await state.set_state(NewOrder.desc)


@router.message(StateFilter(NewOrder.desc))
async def add_item_name(message: types.Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer('Добавьте цену товара')
    await state.set_state(NewOrder.price)


@router.message(StateFilter(NewOrder.price))
async def add_item_name(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await add_product(state)
    await state.clear()
    await message.answer('Товар успешно создан', reply_markup=kb.admin_panel)


@router.message()
async def answer(message: Message):
    await message.reply('Я тебя не понимаю(')
