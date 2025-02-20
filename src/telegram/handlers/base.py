from aiogram import Router, types, F
from aiogram.types import (Message, BotCommand, WebAppData, MenuButtonWebApp, WebAppInfo)

from src.settings import get_settings
from loguru import logger as log
from src.telegram.bot import get_bot

cfg = get_settings()
bot = get_bot()

base_router = Router(name=__name__)


# @base_router.message(F.web_app_data)
# async def web_app_data_handler(message: Message):
#     data: WebAppData = message.web_app_data
#     log.info(f"WebApp data received: {data}")
#     await message.answer(f"WebApp data received: {data.data}")


async def start_telegram() -> None:
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != cfg.webhook_url:
        await bot.set_webhook(
            url=cfg.webhook_url,
            secret_token=cfg.tg_secret_token,
            allowed_updates=base_router.resolve_used_update_types(),
            drop_pending_updates=True,
            max_connections=40 if cfg.debug else 100,
        )

    # Назначаем действие для кнопки меню
    webapp_info = WebAppInfo(url=cfg.webapp_url)
    menu_button = MenuButtonWebApp(text='Play', web_app=webapp_info)
    await bot.set_chat_menu_button(menu_button=menu_button)

    # Задаем список команд
    commands = [
        BotCommand(command="/play", description="Play"),
        BotCommand(command="/reflink", description="My referral link"),
        BotCommand(command="/faq", description="FAQ"),
        BotCommand(command="/support", description="support"),
        BotCommand(command="/policy", description="Политика конфиденциальности"),
    ]
    await bot.set_my_commands(commands)
    log.info("🚀 Telegram bot is running!")



async def end_telegram():
    log.info("⛔ Telegram bot stopping")
    if bot and bot.session:
        # await bot.set_webhook(url='')
        await bot.session.close()
        # await bot.close()


base_router.startup.register(start_telegram)
base_router.shutdown.register(end_telegram)
