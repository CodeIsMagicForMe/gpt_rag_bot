from aiogram.fsm.state import State, StatesGroup


class MenuState(StatesGroup):
    main = State()
    cabinet = State()
    faq = State()


class SupportTicket(StatesGroup):
    waiting_subject = State()
    waiting_description = State()


class ProvisionState(StatesGroup):
    waiting_confirmation = State()
