from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import types, Dispatcher
from handlers import router



class FSMAdmin(StatesGroup):
    name = State()
    photo = State()
    description = State()
    price = State()


@router.message_handler(commands='Загрузить', state=None)
async def cm_start(message: types.Message):
    await  FSMAdmin.photo.set()
    await message.reply('Загрузи фото')


@router.message_handler(content_types=['photo'], state=FSMAdmin.photo)
async def load_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await FSMAdmin.next()
    await message.reply('Теперь введи название')


@router.message_handler(content_types=['photo'], state=FSMAdmin.photo)
async def load_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await FSMAdmin.next()
    await message.reply('Введи описание')


@router.message_handler(content_types=['photo'], state=FSMAdmin.photo)
async def load_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
    await FSMAdmin.next()
    await message.reply('Укажи цену')


@router.message_handler(content_types=['photo'], state=FSMAdmin.photo)
async def load_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = int(message.text)

    async with state.proxy() as data:
        await message.reply(str(data))
    await state.finish()


