from aiogram.fsm.state import State, StatesGroup


class SaleStates(StatesGroup):
    choosing_customer = State()
    adding_items = State()
    choosing_variant = State()
    entering_quantity = State()
    entering_price = State()
    choosing_payment = State()
    confirming = State()


class PurchaseStates(StatesGroup):
    adding_items = State()
    choosing_variant = State()
    entering_quantity = State()
    entering_cost_price = State()
    choosing_payment = State()
    confirming = State()
