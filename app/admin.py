from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import os


class NewOrder(StatesGroup):
    type = State()
    name = State()
    brand = State()
    photo = State()
    desc = State()
    price = State()


async def check_user_is_admin(message: Message):
    if message.from_user.id != int(os.getenv('ADMIN_ID')):
        await message.answer(f'Вы не являетесь администратором')
        return False
    return True
