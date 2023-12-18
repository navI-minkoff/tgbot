import json
import os

from aiogram import Router, F, Dispatcher, types, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import app.keyboards as kb
from app.database.requests import get_product, add_product, get_brand, delete_product, add_user_to_db
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from app.database.models import Base
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.admin import check_user_is_admin, NewOrder


bot = Bot(token=os.getenv('TOKEN'), parse_mode='HTML')

memory_storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=memory_storage)


# class NewOrder(StatesGroup):
#     type = State()
#     name = State()
#     brand = State()
#     photo = State()
#     desc = State()
#     price = State()


@router.message(F.text == 'Отмена')
async def contacts(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer('Действие отменено', reply_markup=kb.admin_panel)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f'{message.from_user.first_name}, добро пожаловать!', reply_markup=kb.main)
    await add_user_to_db(message.from_user.id)


@router.message(Command('admin'))
async def admin(message: Message):
    if await check_user_is_admin(message):
        await message.answer('Вы авторизовались как администратор', reply_markup=kb.admin_panel)


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
    if await check_user_is_admin(message):
        await message.answer('Вы вошли в админ-панель', reply_markup=kb.admin_panel)


@router.callback_query(F.data.startswith('category_'))
async def category_selected(callback: CallbackQuery):
    category_id = callback.data.split('_')[1]
    await callback.message.answer(f'Товары по выбранной категории:', reply_markup=await kb.products(category_id))
    await callback.answer('')


@router.callback_query(F.data.startswith('del '))
async def del_product(callback: CallbackQuery):
    product_id = callback.data.split(' ')[1]
    confirmation_keyboard = InlineKeyboardBuilder()
    confirmation_keyboard.add(
        InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_del {product_id}'),
        InlineKeyboardButton(text='Отмена', callback_data='cancel_del')
    )
    await callback.message.answer('Вы уверены, что хотите удалить данный товар?',
                                  reply_markup=confirmation_keyboard.adjust(2).as_markup())


@router.callback_query(F.data.startswith('confirm_del '))
async def confirm_del_product(callback: CallbackQuery):
    product_id = callback.data.split(' ')[1]
    await delete_product(product_id)
    await callback.message.answer('Товар удален', reply_markup=kb.admin_panel)


@router.callback_query(F.data == 'cancel_del')
async def cancel_del_product(callback: CallbackQuery):
    await callback.message.answer('Удаление товара отменено', reply_markup=kb.admin_panel)


@router.callback_query(F.data.startswith('product_'))
async def product_selected(callback: CallbackQuery):
    product_id = callback.data.split('_')[1]
    product = await get_product(product_id=product_id)
    brand = await get_brand(product.brand_id)
    if callback.from_user.id == int(os.getenv('ADMIN_ID')):
        await bot.send_photo(callback.from_user.id, product.photo,
                             caption=f'<b>{product.name}</b>\n\nБренд:<b>{brand.name}</b>\n\n{product.description}\n\nЦена: {product.price} руб',
                             reply_markup=InlineKeyboardBuilder().add(InlineKeyboardButton(text=f'Удалить',
                                                                                           callback_data=f'del {product.id}')).as_markup())
    else:
        await bot.send_photo(callback.from_user.id, product.photo,
                             caption=f'<b>{product.name}</b>\n\nБренд:<b>{brand.name}</b>\n\n{product.description}\n\nЦена: {product.price} руб')
    await callback.answer(f'Вы выбрали {product.name}')


@router.message(StateFilter(None), F.text == 'Добавить товар')
async def add_item(message: types.Message, state: FSMContext):
    if await check_user_is_admin(message):
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
async def add_item_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer('Добавьте размеры товара в формате JSON (например, {"S": 10, "M": 15, "L": 20})')
    await state.set_state(NewOrder.sizes)


@router.message(StateFilter(NewOrder.sizes))
async def add_item_sizes(message: types.Message, state: FSMContext):
    try:
        sizes_json = json.loads(message.text)
    except json.JSONDecodeError:
        await message.answer('Некорректный формат JSON. Пожалуйста, введите размеры в правильном формате.')
        return

    await state.update_data(sizes=sizes_json)
    await add_product(state)
    await state.clear()
    await message.answer('Товар успешно создан', reply_markup=kb.admin_panel)


# @router.message(StateFilter(NewOrder.price))
# async def add_item_name(message: types.Message, state: FSMContext):
#     await state.update_data(price=message.text)
#     await add_product(state)
#     await state.clear()
#     await message.answer('Товар успешно создан', reply_markup=kb.admin_panel)


@router.message(F.text == 'Удалить товар')
async def admin_panel(message: Message):
    if await check_user_is_admin(message):
        await message.answer('Выберете вариант из каталога', reply_markup=await kb.categories(False))
    else:
        return


@router.message()
async def answer(message: Message):
    await message.reply('Я тебя не понимаю(')
