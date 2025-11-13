from aiogram import Router

from bot.handlers import register_common_handlers, set_handler_context
from bot.services.api_clients import BillingAPI, ProvisionerAPI
from config import Config


def create_router(config: Config, billing: BillingAPI, provisioner: ProvisionerAPI) -> Router:
    """Configure router with shared dependencies and handlers."""

    set_handler_context(config=config, billing=billing, provisioner=provisioner)
    router = Router(name="main")
    register_common_handlers(router)
    return router


__all__ = ["create_router"]
