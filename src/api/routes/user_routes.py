from typing import Any, Optional, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse

from src.core.dependencies import get_current_user, get_current_superuser
from src.core.enums import RatingType
from src.core.schemas import Pagination
from src.api.schemas.user_schemas import (UserUpdate, UserBalanceUpdate, User, UserCreate)
from src.api.services.user_service import UserService

from src.settings import get_settings

cfg = get_settings()


user_router = APIRouter(tags=["Users"], prefix="/user")

if cfg.run_type != 'local':
    from src.telegram.bot import get_bot
    # from aiogram.utils.deep_linking import create_start_link


@user_router.post("/create")
async def create_user(
        user: Dict[str, int] = Depends(get_current_user),
        new_user: UserCreate = Depends(UserCreate)
) -> Optional[User]:
    """
    Создание нового пользователя с проверкой его наличия
    """
    new_user = await UserService.create_user(new_user)
    return new_user


@user_router.post("/me")
async def get_user(
        user: Dict[str, Any] = Depends(get_current_user),
) -> ORJSONResponse:
    """
    Получение пользователя
    """
    db_user = await UserService.get_user_by_telegram_id(user.get("tg_id"))
    return ORJSONResponse(content=db_user)


@user_router.get("/getReflink")
async def get_referral_link(
        user: Dict[str, Any] = Depends(get_current_user),
) -> str:
    """
    Получение реферальной ссылки пользователя по telegram id
    """
    username = (await get_bot().me()).username
    reflink = f"t.me/{username}/{cfg.webapp_username}?startapp={user.get('tg_id')}"
    return reflink


@user_router.patch("/update")
async def update_user_by_telegram_id(
        user: Dict[str, Any] = Depends(get_current_user),
        upd: UserUpdate = Depends(UserUpdate)
) -> Any:
    """
    Обновление данных пользователя по telegram id
    """
    updated_user = await UserService.update_user_by_telegram_id(
        tg_id=user.get("tg_id"),
        user_update=upd,
    )
    return ORJSONResponse(content=updated_user)


@user_router.post("/updateGameBalance")
async def update_game_balance(
        user: Dict[str, Any] = Depends(get_current_user),
        balance: UserBalanceUpdate = Depends(UserBalanceUpdate)
) -> dict:
    """
    Обновление баланса игровой валюты юзера.\n\n

    Входные параметры:\n
    current_tap_count - текущее значение счетчика тапов, которое сделал юзер \n\n

    """
    # tap_count = await redis.get(tg_id)
    res = await UserService.update_game_balance(
        tg_id=user.get("tg_id"), new_tap_count=balance.current_tap_count)
    return res


@user_router.get("/getReferralStats")
async def get_referrals_stats_by_telegram_id(
        user: Dict[str, Any] = Depends(get_current_user),
) -> ORJSONResponse:
    """
    Получение статистики по рефералам юзера\n
    """
    stat = await UserService.get_referral_stats(
        tg_id=user.get("tg_id"),
    )
    return ORJSONResponse(content=stat)

