import time
from datetime import datetime, timezone
from typing import Optional, Any, Dict, Callable

from jose import jwt
from aiogram.utils.web_app import WebAppInitData
from fastapi.security.http import HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException, status, Request
from requests import Request

from src.core.exceptions import InvalidTokenException, TokenExpiredException
from src.api.auth import tg_auth_schema, verify_init_data, oauth2_scheme
from src.api.schemas.user_schemas import User
from src.api.services.user_service import UserService
from src.settings import get_settings
from loguru import logger as log

cfg = get_settings()


async def get_webapp_data(
    auth_cred: HTTPAuthorizationCredentials = Depends(tg_auth_schema)
) -> Optional[WebAppInitData]:
    if auth_cred is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Empty initData"
        )

    webapp_data: WebAppInitData = await verify_init_data(auth_cred)

    # Проверяем время жизни initData
    auth_timestamp = int(webapp_data.auth_date.timestamp())
    if auth_timestamp < (int(time.time()) - (3 * 3600)):  # 3 часа на проверку
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="InitData is outdated")

    await UserService.telegram_auth(webapp_data.user.id, auth_timestamp)
    return webapp_data


async def get_current_user(
        token: str = Depends(oauth2_scheme),
) -> Optional[Any]:
    try:
        payload = jwt.decode(
            str(token),
            cfg.SECRET_KEY,
            algorithms=[cfg.ALGORITHM]
        )

        # Проверка на истечение токена
        exp = payload.get("exp")
        if exp is not None and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(tz=timezone.utc):
            raise TokenExpiredException

        user_id = payload.get("sub")
        tg_id = int(payload.get("tg_id"))
        if user_id is None:
            raise InvalidTokenException

    except jwt.ExpiredSignatureError:
        raise TokenExpiredException
    except Exception:
        raise InvalidTokenException

    # current_user = await UserService.get_user_by_id(user_id)
    # if not current_user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")

    return dict(user_id=user_id, tg_id=tg_id)


async def get_current_superuser(
        user: Dict[str, Any] = Depends(get_current_user),
) -> User:
    db_user = await UserService.check_user(user_id=str(user.get("user_id")))
    if not db_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges")

    return db_user


async def get_current_active_user(
        user: Dict[str, Any] = Depends(get_current_user),
) -> User:
    db_user = await UserService.check_user(user_id=str(user.get("user_id")))
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    return db_user
