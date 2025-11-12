from __future__ import annotations

from enum import Enum

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuAction(str, Enum):
    TRIAL = "trial"
    CABINET = "cabinet"
    FAQ = "faq"
    SUPPORT = "support"


class CabinetAction(str, Enum):
    DOWNLOAD = "download"
    EXTEND = "extend"
    CHANGE_NODE = "change_node"
    BACK = "back"


class ProvisionAction(str, Enum):
    CONFIRM = "confirm"
    CANCEL = "cancel"


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎟️ Trial", callback_data=f"menu:{MenuAction.TRIAL.value}")
    builder.button(text="👤 Личный кабинет", callback_data=f"menu:{MenuAction.CABINET.value}")
    builder.button(text="ℹ️ FAQ", callback_data=f"menu:{MenuAction.FAQ.value}")
    builder.button(text="🆘 Поддержка", callback_data=f"menu:{MenuAction.SUPPORT.value}")
    builder.adjust(2)
    return builder.as_markup()


def cabinet_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬇️ Скачать конфиг", callback_data=f"cab:{CabinetAction.DOWNLOAD.value}")
    builder.button(text="⭐ Продлить", callback_data=f"cab:{CabinetAction.EXTEND.value}")
    builder.button(text="🛰 Сменить узел", callback_data=f"cab:{CabinetAction.CHANGE_NODE.value}")
    builder.button(text="⬅️ Назад", callback_data=f"cab:{CabinetAction.BACK.value}")
    builder.adjust(1)
    return builder.as_markup()


def provision_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Получить", callback_data=f"prov:{ProvisionAction.CONFIRM.value}")
    builder.button(text="Отмена", callback_data=f"prov:{ProvisionAction.CANCEL.value}")
    builder.adjust(2)
    return builder.as_markup()
