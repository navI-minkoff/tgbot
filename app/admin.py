from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
import os

ADMIN_MODE = False


def update_global_variable(new_value):
    global ADMIN_MODE
    ADMIN_MODE = new_value


def get_global_variable():
    global ADMIN_MODE
    return ADMIN_MODE


class NewOrder(StatesGroup):
    type = State()
    name = State()
    brand = State()
    photo = State()
    desc = State()
    price = State()
    sizes = State()


async def check_admin_mod_on(callback: CallbackQuery):
    global ADMIN_MODE
    if callback.from_user.id != int(os.getenv('ADMIN_ID')):
        return False
    elif ADMIN_MODE:
        return True
    else:
        return False
