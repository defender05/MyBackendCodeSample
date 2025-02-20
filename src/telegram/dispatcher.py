from functools import lru_cache
from aiogram import Dispatcher
from aiogram.fsm.storage.redis import Redis, RedisStorage
from src.settings import get_settings, Settings
from src.telegram.handlers.base import base_router
from src.telegram.handlers.commands import commands_router
from src.telegram.handlers.payments import payment_router

cfg: Settings = get_settings()

redis = Redis(host=cfg.redis_host, port=cfg.redis_port, db=1)
storage = RedisStorage(redis=redis)

dp = Dispatcher(storage=storage)
dp.include_router(base_router)
dp.include_router(commands_router)
dp.include_router(payment_router)


@lru_cache()
def get_dispatcher() -> Dispatcher:
    return dp
