from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    SuccessfulPayment,
)
from aiogram.fsm.context import FSMContext

from config import Config
from bot.keyboards import (
    CabinetAction,
    MenuAction,
    ProvisionAction,
    cabinet_kb,
    main_menu_kb,
    provision_confirm_kb,
)
from bot.services.api_clients import (
    APIClientError,
    BillingAPI,
    ProvisionBundle,
    ProvisionerAPI,
)
from bot.states import MenuState, ProvisionState, SupportTicket


logger = logging.getLogger(__name__)


@dataclass
class HandlerContext:
    config: Config
    billing: BillingAPI
    provisioner: ProvisionerAPI


_handler_context: Optional[HandlerContext] = None


def create_router(config: Config, billing: BillingAPI, provisioner: ProvisionerAPI) -> Router:
    global _handler_context
    _handler_context = HandlerContext(config=config, billing=billing, provisioner=provisioner)
    router = Router(name="main")
    register_common_handlers(router)
    return router


def register_common_handlers(router: Router) -> None:
    router.message.register(cmd_start, CommandStart())
    router.message.register(request_trial_command, Command("trial"))
    router.message.register(show_terms_command, Command("terms"))
    router.message.register(show_privacy_command, Command("privacy"))
    router.message.register(handle_support_subject, SupportTicket.waiting_subject)
    router.message.register(handle_support_description, SupportTicket.waiting_description)

    router.callback_query.register(handle_menu_callback, F.data.startswith("menu:"))
    router.callback_query.register(handle_cabinet_callback, F.data.startswith("cab:"))
    router.callback_query.register(handle_provision_callback, F.data.startswith("prov:"))

    router.pre_checkout_query.register(answer_pre_checkout)
    router.message.register(process_successful_payment, F.successful_payment)


async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.set_state(MenuState.main)
    ctx = _require_context()
    greeting_lines = [
        "👋 Привет! Я помогу управлять подпиской. Выберите действие:",
        "",
        ctx.config.data_usage_notice,
    ]
    await message.answer("\n".join(greeting_lines), reply_markup=main_menu_kb())


async def handle_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    action_value = callback.data.split(":", 1)[1]
    action = MenuAction(action_value)
    if action is MenuAction.TRIAL:
        await _handle_trial(callback.message, state)
    elif action is MenuAction.CABINET:
        await show_cabinet(callback.message, state)
    elif action is MenuAction.FAQ:
        await show_faq(callback.message, state)
    elif action is MenuAction.SUPPORT:
        await start_support_flow(callback.message, state)
    elif action is MenuAction.TERMS:
        await show_terms(callback.message, state)
    elif action is MenuAction.PRIVACY:
        await show_privacy(callback.message, state)
    await callback.answer()


async def show_faq(message: Message, state: FSMContext) -> None:
    await state.set_state(MenuState.faq)
    config = _require_context().config
    await message.answer(config.faq_text, reply_markup=main_menu_kb())


async def request_trial_command(message: Message, state: FSMContext) -> None:
    await _handle_trial(message, state)


async def show_terms(message: Message, state: FSMContext) -> None:
    await state.set_state(MenuState.main)
    config = _require_context().config
    text = (
        "📄 <b>Условия использования</b>\n"
        f"{config.terms_url}\n\n"
        f"{config.data_usage_notice}"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode=ParseMode.HTML)


async def show_privacy(message: Message, state: FSMContext) -> None:
    await state.set_state(MenuState.main)
    config = _require_context().config
    text = (
        "🔐 <b>Политика конфиденциальности</b>\n"
        f"{config.privacy_url}\n\n"
        f"{config.data_usage_notice}"
    )
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode=ParseMode.HTML)


async def show_terms_command(message: Message, state: FSMContext) -> None:
    await show_terms(message, state)


async def show_privacy_command(message: Message, state: FSMContext) -> None:
    await show_privacy(message, state)


async def _handle_trial(message: Message, state: FSMContext) -> None:
    await state.set_state(MenuState.main)
    ctx = _require_context()
    try:
        info = await ctx.billing.start_trial(message.from_user.id)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Trial request failed",
            extra={"tg_id": message.from_user.id, "error_type": type(exc).__name__},
        )
        await message.answer("Не удалось выдать trial. Попробуйте позже.")
        return
    status_text = "Trial активирован ✅" if info.activated else "Trial уже был активирован"
    expires_text = f"Доступ действует до: {info.expires_at}" if info.expires_at else ""
    await message.answer(
        "\n".join(filter(None, [status_text, info.message, expires_text])),
        reply_markup=main_menu_kb(),
    )


async def show_cabinet(message: Message, state: FSMContext) -> None:
    await state.set_state(MenuState.cabinet)
    ctx = _require_context()
    try:
        status = await ctx.billing.subscription_status(message.from_user.id)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Failed to fetch subscription status",
            extra={"tg_id": message.from_user.id, "error_type": type(exc).__name__},
        )
        await message.answer("Не удалось получить статус подписки", reply_markup=main_menu_kb())
        return

    text_lines = ["<b>Личный кабинет</b>"]
    text_lines.append(f"Статус: {status.status}")
    if status.expires_at:
        text_lines.append(f"Доступ до: {status.expires_at}")
    if status.plan:
        text_lines.append(f"Тариф: {status.plan}")
    if status.is_trial:
        text_lines.append("Режим: Trial")
    await message.answer("\n".join(text_lines), reply_markup=cabinet_kb())


async def handle_cabinet_callback(callback: CallbackQuery, state: FSMContext) -> None:
    action_value = callback.data.split(":", 1)[1]
    action = CabinetAction(action_value)
    if action is CabinetAction.DOWNLOAD:
        await ask_provision_confirmation(callback.message, state, node=None)
    elif action is CabinetAction.CHANGE_NODE:
        await ask_provision_confirmation(callback.message, state, node="rotate")
    elif action is CabinetAction.EXTEND:
        await send_stars_invoice(callback.message)
    elif action is CabinetAction.BACK:
        await cmd_start(callback.message, state)
    await callback.answer()


async def ask_provision_confirmation(message: Message, state: FSMContext, node: Optional[str]) -> None:
    await state.update_data(provision_node=node)
    await state.set_state(ProvisionState.waiting_confirmation)
    text = "Сформировать новый конфиг?" if node else "Отправить последний конфиг?"
    await message.answer(text, reply_markup=provision_confirm_kb())


async def handle_provision_callback(callback: CallbackQuery, state: FSMContext) -> None:
    action_value = callback.data.split(":", 1)[1]
    action = ProvisionAction(action_value)
    if action is ProvisionAction.CANCEL:
        await show_cabinet(callback.message, state)
        await callback.answer("Отмена")
        return

    data = await state.get_data()
    node = data.get("provision_node")
    await send_provision(callback.message, node=node)
    await show_cabinet(callback.message, state)
    await callback.answer("Готово")


async def send_provision(message: Message, node: Optional[str]) -> None:
    ctx = _require_context()
    try:
        bundle = await ctx.provisioner.provision(message.from_user.id, node=node)
    except APIClientError as exc:
        await message.answer(str(exc))
        return
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Provision request failed",
            extra={"tg_id": message.from_user.id, "error_type": type(exc).__name__, "node": node},
        )
        await message.answer("Не удалось получить конфиг. Попробуйте позже.")
        return

    await _send_config_bundle(message.bot, message.chat.id, bundle)


async def _send_config_bundle(bot: Bot, chat_id: int, bundle: ProvisionBundle) -> None:
    document = BufferedInputFile(bundle.file_bytes, filename=bundle.file_name)
    await bot.send_document(chat_id, document=document)
    if bundle.qr_bytes:
        qr = BufferedInputFile(bundle.qr_bytes, filename="config_qr.png")
        await bot.send_photo(chat_id, photo=qr, caption="QR для быстрой настройки")


async def send_stars_invoice(message: Message) -> None:
    ctx = _require_context()
    plan = ctx.config.subscription_plan
    payload = plan.payload
    prices = [LabeledPrice(label=plan.title, amount=plan.price_stars)]
    provider_token = ctx.config.payment_provider_token or "STARS"
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title=plan.title,
        description=plan.description,
        payload=payload,
        currency="XTR",
        prices=prices,
        provider_token=provider_token,
        start_parameter="stars_sub",
    )


async def answer_pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot) -> None:
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def process_successful_payment(message: Message, state: FSMContext) -> None:
    payment: SuccessfulPayment = message.successful_payment
    stars_tx_id = None
    if payment.stars_app_payment:
        stars_tx_id = payment.stars_app_payment.stars_transaction_id
    if not stars_tx_id:
        stars_tx_id = payment.telegram_payment_charge_id
    ctx = _require_context()
    try:
        await ctx.billing.confirm_stars_payment(
            user_id=message.from_user.id,
            stars_tx_id=stars_tx_id,
            payload=payment.invoice_payload,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Failed to confirm payment",
            extra={
                "tg_id": message.from_user.id,
                "stars_tx_id": stars_tx_id,
                "error_type": type(exc).__name__,
            },
        )
        await message.answer("Платёж получен, но не удалось подтвердить его в биллинге. Поддержка уже уведомлена.")
        await message.bot.send_message(
            ctx.config.admin_chat_id,
            f"Не удалось подтвердить оплату пользователя {message.from_user.id} (tx: {stars_tx_id})",
        )
        return

    await message.answer(
        "Спасибо за оплату! Подписка будет продлена в течение пары минут.",
        reply_markup=cabinet_kb(),
    )
    await show_cabinet(message, state)


async def start_support_flow(message: Message, state: FSMContext) -> None:
    await state.set_state(SupportTicket.waiting_subject)
    await message.answer("Опишите тему обращения", reply_markup=None)


async def handle_support_subject(message: Message, state: FSMContext) -> None:
    await state.update_data(ticket_subject=message.text)
    await state.set_state(SupportTicket.waiting_description)
    await message.answer("Расскажите подробнее о проблеме")


async def handle_support_description(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    subject = data.get("ticket_subject", "Без темы")
    description = message.text or "(пусто)"
    ctx = _require_context()
    text = (
        "🆘 <b>Новый тикет</b>\n"
        f"От: {message.from_user.full_name} ({message.from_user.id})\n"
        f"Тема: {subject}\n\n{description}"
    )
    await message.bot.send_message(ctx.config.admin_chat_id, text, parse_mode=ParseMode.HTML)
    await message.answer("Спасибо! Поддержка скоро ответит.", reply_markup=main_menu_kb())
    await state.set_state(MenuState.main)


def _require_context() -> HandlerContext:
    if not _handler_context:
        raise RuntimeError("Router context is not configured")
    return _handler_context
