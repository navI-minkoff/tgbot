from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
import os
import yadisk

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


class Config(StatesGroup):
    user_id = State()
    track_config = State()
    custom = State()


async def check_admin_mod_on(user_id):
    global ADMIN_MODE
    if user_id != int(os.getenv('ADMIN_ID')):
        return False
    elif ADMIN_MODE:
        return True
    else:
        return False


async def create_backup(local_file_path, remote_file_path):
    disk = yadisk.YaDisk(token=os.getenv('YANDEX_TOKEN'))
    try:
        disk.upload(local_file_path, remote_file_path)
        print("Файл успешно загружен на Яндекс.Диск.")
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
