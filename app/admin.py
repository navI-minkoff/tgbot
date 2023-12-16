from aiogram.fsm.state import State, StatesGroup
class NewOrder(StatesGroup):
    type = State()
    name = State()
    brand = State()
    photo = State()
    desc = State()
    price = State()





