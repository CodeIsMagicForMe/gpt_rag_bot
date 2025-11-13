import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot import create_router
from bot.services.api_clients import BillingAPI, ProvisionerAPI
from config import load_config

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    config = load_config()
    bot = Bot(token=config.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    billing = BillingAPI(config.billing_base_url)
    provisioner = ProvisionerAPI(config.provisioner_base_url)

    dp.include_router(create_router(config=config, billing=billing, provisioner=provisioner))

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
