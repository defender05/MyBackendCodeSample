import sys
import logging as log
from functools import lru_cache
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from src.settings import get_settings, Settings

log.basicConfig(level=log.INFO, stream=sys.stdout)

cfg: Settings = get_settings()

# class UserMiddleware(BaseMiddleware):
#     async def __call__(
#             self,
#             handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
#             event: Message,
#             data: Dict[str, Any]
#     ) -> Any:
#         if not event.from_user.username:
#             return await event.answer("Нельзя использовать бота без ника")
#
#         user = dict(
#             id=event.from_user.id,
#             name=event.from_user.username,
#             tg_url=event.from_user.url,
#             chat_id=event.chat.id
#         )
#         # Ключи в словаре data можно юзать как входные параметры в обработчиках
#         data["user"] = user
#         return await handler(event, data)

bot = Bot(cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


@lru_cache()
def get_bot() -> Bot:
    return bot

# Пример ограничения доступа к боту только для определенных пользователей
# acl = (111111111,)
# admin_only = lambda message: message.from_user.id not in acl
# @dp.message_handler(admin_only, content_types=['any'])
# async def handle_unwanted_users(message: types.Message):
#     await config.bot.delete_message(message.chat.id, message.message_id)
#     return

