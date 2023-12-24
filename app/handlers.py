import json
import os

from aiogram import Router, F, Dispatcher, types, Bot
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import app.keyboards as kb
from app.database.requests import get_product, add_product, get_brand, delete_product, add_user_to_db, \
    add_product_in_cart, check_product, get_products_in_cart_user, count_values_in_json, get_sizes_str, \
    delete_product_in_cart, is_numeric, add_custom_and_departures, clear_cart_and_update_product
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from app.database.models import Base
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.admin import check_admin_mod_on, NewOrder, update_global_variable, get_global_variable, Config

bot = Bot(token=os.getenv('TOKEN'), parse_mode='HTML')

memory_storage = MemoryStorage()
dp = Dispatcher(storage=memory_storage)
router = Router()


@router.message(F.text == 'Отмена')
async def contacts(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer('Действие отменено', reply_markup=kb.admin_panel)


@router.message(CommandStart())
async def cmd_start(message: Message):
    if get_global_variable():
        update_global_variable(False)
    firs_mess = ', добро пожаловать!'
    if await add_user_to_db(message.from_user.id):
        firs_mess = ', с возвращением!'
    await message.answer(f'{message.from_user.first_name}' + firs_mess, reply_markup=kb.main)


@router.message(Command('admin'))
async def admin(message: Message):
    is_admin_mod_on = get_global_variable()
    if message.from_user.id == int(os.getenv('ADMIN_ID')):
        if is_admin_mod_on:
            update_global_variable(False)
            await message.answer('Вы вышли из админ-панели', reply_markup=kb.main)
        else:
            update_global_variable(True)
            await message.answer('Вы авторизовались как администратор', reply_markup=kb.admin_panel)


@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выберете вариант из каталога', reply_markup=await kb.categories(False))


@router.message(F.text == 'Корзина')
async def print_cart(message: Message):
    products_in_cart = await get_products_in_cart_user(message.from_user.id)
    price = 0
    for product_in_cart in products_in_cart:
        product = await get_product(product_in_cart.product_id)
        brand = await get_brand(product.brand_id)
        price += int(product.price * count_values_in_json(product_in_cart.size))
        sizes = get_sizes_str(product_in_cart.size)
        await bot.send_photo(message.from_user.id, product.photo,
                             caption=f'<b>{product.name}</b>\n\n<b>Бренд</b>: <i>{brand.name}</i>\n\n{product.description}\n'
                                     f'\n<b>Выбранные размеры: </b>{sizes}\n\n<b>Цена</b>: {product.price} руб',
                             reply_markup=InlineKeyboardBuilder().add(InlineKeyboardButton(
                                 text=f'Удалить',
                                 callback_data=f'del_product_in_cart {product_in_cart.product_id}')).as_markup())

    if price == 0:
        await message.answer(f'Ваша корзина пуста', reply_markup=kb.main)
    else:
        await message.answer(f'Сумма заказа: {price} руб', reply_markup=kb.cart_panel)


@router.message(F.text == 'Контакты')
async def contacts(message: Message):
    await message.answer('Номер телефона')


@router.message(F.text == 'Заказать')
async def contacts(message: Message):
    confirmation_keyboard = InlineKeyboardBuilder()
    confirmation_keyboard.add(
        InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_custom_products'),
        InlineKeyboardButton(text='Отмена', callback_data='cancel_custom_products')
    )
    await message.answer('Вы уверены, что хотите заказать данные товары?',
                         reply_markup=confirmation_keyboard.adjust(2).as_markup())


@router.callback_query(F.data.startswith('confirm_custom_products'))
async def confirm_del_product(callback: CallbackQuery):
    await callback.message.edit_text('В ближайшее время с вами свяжется наш сотрудник')
    confirmation_keyboard = InlineKeyboardBuilder()
    confirmation_keyboard.add(
        InlineKeyboardButton(text='Ввести трек номер', callback_data=f'confirm_custom {callback.from_user.id}'),
        InlineKeyboardButton(text='Отмена', callback_data='cancel_custom')
    )
    products_in_cart = await get_products_in_cart_user(callback.from_user.id)

    cart_info = "Список заказанных товаров:\n"
    price = 0
    if products_in_cart:
        for product_in_cart in products_in_cart:
            product = await get_product(product_in_cart.product_id)
            price += int(product.price * count_values_in_json(product_in_cart.size))
            selected_sizes = ', '.join(f"{key}:{value}" for key, value in product_in_cart.size.items())
            cart_info += f"{product.name}: {selected_sizes}\n"

    await bot.send_message(os.getenv('CHAT_ID'), f'@{callback.from_user.username} сделал заказ.' + cart_info +
                           f'Сумма заказа: {price}',
                           reply_markup=confirmation_keyboard.adjust(2).as_markup())


@router.callback_query(F.data.startswith('cancel_custom_products'))
async def confirm_del_product(callback: CallbackQuery):
    await callback.message.edit_text('Заказ отменен')


@router.callback_query(F.data.startswith('confirm_custom '))
async def confirm_custom(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Config.user_id)
    user_id = callback.data.split(' ')[1]
    await state.update_data(user_id=user_id)
    await state.set_state(Config.track_config)
    await callback.message.answer('Введите трек заказа:')


@router.message(StateFilter(Config.track_config))
async def add_item_type(message: Message, state: FSMContext):
    await state.update_data(track_config=message.text)
    try:
        await state.update_data(custom=True)
    except Exception as e:
        await message.answer(f'Ошибка f{e}')
        await state.update_data(confirm_custom=False)

    if Config.custom:
        data = await state.get_data()
        user_id = data['user_id']
        track_config = data['track_config']
        custom = data['custom']
        products_in_cart = await get_products_in_cart_user(message.from_user.id)

        await message.answer(f'Заказ оформлен  {user_id}, {track_config}, {custom}')
        price = 0
        product_ids = []
        for product_in_cart in products_in_cart:
            product = await get_product(product_in_cart.product_id)
            product_ids.append(product.id)
            price += int(product.price * count_values_in_json(product_in_cart.size))

        await add_custom_and_departures(user_id, price, track_config, product_ids)
        await clear_cart_and_update_product(user_id)

        await state.clear()


@router.callback_query(F.data.startswith('cancel_custom'))
async def confirm_del_product(callback: CallbackQuery):
    await callback.message.edit_text('Отмена заказа')


@router.message(F.text == 'Админ-панель')
async def admin_panel(message: Message):
    if await check_admin_mod_on(message.from_user.id):
        await message.answer('Вы вошли в админ-панель', reply_markup=kb.admin_panel)


@router.message(F.text == 'Назад в меню')
async def admin_panel(message: Message):
    await message.answer('Вы вернулись в меню', reply_markup=kb.main)


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
        InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_del_by_admin {product_id}'),
        InlineKeyboardButton(text='Отмена', callback_data='cancel_del_by_admin')
    )
    await callback.message.answer('Вы уверены, что хотите удалить данный товар?',
                                  reply_markup=confirmation_keyboard.adjust(2).as_markup())


@router.callback_query(F.data.startswith('confirm_del_by_admin '))
async def confirm_del_product(callback: CallbackQuery):
    product_id = callback.data.split(' ')[1]
    await delete_product(product_id)
    await callback.message.answer('Товар удален', reply_markup=kb.admin_panel)


@router.callback_query(F.data.startswith('del_product_in_cart '))
async def del_product(callback: CallbackQuery):
    product_id = callback.data.split(' ')[1]
    confirmation_keyboard = InlineKeyboardBuilder()
    confirmation_keyboard.add(
        InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_del_product_in_cart {product_id}'),
        InlineKeyboardButton(text='Отмена', callback_data='cancel_del_product_in_cart')
    )
    await callback.message.answer('Вы уверены, что хотите удалить данный товар?',
                                  reply_markup=confirmation_keyboard.adjust(2).as_markup())


@router.callback_query(F.data == 'cancel_del_product_in_cart')
async def cancel_del_product(callback: CallbackQuery):
    await callback.message.edit_text('Удаление товара отменено')


@router.callback_query(F.data.startswith('confirm_del_product_in_cart '))
async def confirm_del_product(callback: CallbackQuery):
    product_id = callback.data.split(' ')[1]
    await delete_product_in_cart(product_id, callback.from_user.id)
    await callback.message.edit_text('Товар удален')


@router.callback_query(F.data == 'cancel_del_by_admin')
async def cancel_del_product(callback: CallbackQuery):
    await callback.message.answer('Удаление товара отменено', reply_markup=kb.admin_panel)


@router.callback_query(F.data.startswith('size_selection '))
async def product_size_selection(callback: CallbackQuery):
    product_id = callback.data.split(' ')[1]
    product = await get_product(product_id)

    product_sizes = product.sizes
    available_sizes = [size for size, quantity in product_sizes.items() if quantity != 0]
    sizes_keyboard = InlineKeyboardBuilder()
    for size_name in available_sizes:
        sizes_keyboard.add(
            InlineKeyboardButton(text=f'{size_name}', callback_data=f'add_product {product_id} {size_name}'))

    await callback.message.answer(text='Выберите размер:', reply_markup=sizes_keyboard.adjust(2).as_markup())


@router.callback_query(F.data.startswith('add_product '))
async def add_product_in_user_cart(callback: CallbackQuery):
    product_id = callback.data.split(' ')[1]
    selected_size = callback.data.split(' ')[2]
    await add_product_in_cart(user_id=callback.from_user.id, product_id=product_id, product_size=selected_size)
    await callback.message.answer(f'Товар добавлен в корзину')


@router.callback_query(F.data.startswith('product_'))
async def product_selected(callback: CallbackQuery):
    product_id = callback.data.split('_')[1]
    product = await get_product(product_id=product_id)
    brand = await get_brand(product.brand_id)
    check = await check_admin_mod_on(callback.from_user.id)
    if check:
        await bot.send_photo(callback.from_user.id, product.photo,
                             caption=f'<b>{product.name}</b>\n\n<b>Бренд</b>: <i>{brand.name}</i>\n\n{product.description}\n'
                                     f'\n<b>Цена</b>: {product.price} руб',
                             reply_markup=InlineKeyboardBuilder().add(InlineKeyboardButton(text=f'Удалить',
                                                                                           callback_data=f'del {product.id}')).as_markup())
    else:
        await bot.send_photo(callback.from_user.id, product.photo,
                             caption=f'<b>{product.name}</b>\n\n<b>Бренд</b>: <i>{brand.name}</i>\n\n{product.description}\n'
                                     f'\n<b>Цена</b>: {product.price} руб',
                             reply_markup=InlineKeyboardBuilder().add(InlineKeyboardButton(text=f'В корзину',
                                                                                           callback_data=f'size_selection {product.id}')).as_markup()
                             )
    await callback.answer(f'Вы выбрали {product.name}')


@router.message(StateFilter(None), F.text == 'Добавить товар')
async def add_item(message: types.Message, state: FSMContext):
    if await check_admin_mod_on(message.from_user.id):
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
    if await check_product(state):
        await message.answer(f'Такой товар уже существует', reply_markup=kb.admin_panel)
        await state.clear()
    else:
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
    if is_numeric(message.text):
        await state.update_data(price=message.text)
        await message.answer(
            'Добавьте размеры товара в формате JSON (например, для одежды: {"S": 10, "M": 15, "L": 20}\n'
            'для обуви: {"40": 10, "41": 15, "42": 20})')
        await state.set_state(NewOrder.sizes)
    else:
        await message.answer('Неправильный формат. Введите только число')


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
    if await check_admin_mod_on(message.from_user.id):
        await message.answer('Выберете вариант из каталога', reply_markup=await kb.categories(False))
    else:
        return


@router.message()
async def answer(message: Message):
    await message.reply('Я тебя не понимаю(')
