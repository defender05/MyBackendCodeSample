import uuid
from typing import Dict, Any

from aiogram.utils.web_app import WebAppInitData
from fastapi import Request, Response, APIRouter, Depends, HTTPException, status
from src.core.dependencies import get_current_user, get_current_active_user, get_webapp_data
from src.core.exceptions import InvalidCredentialsException
from src.core.models import UserModel
from src.api.schemas.auth_schemas import Token
from src.api.services.auth_service import AuthService
from src.settings import get_settings

cfg = get_settings()


auth_router = APIRouter(tags=["Auth"], prefix="/auth")


# @auth_router.post("/register", status_code=status.HTTP_201_CREATED)
# async def register(
#     user: UserCreate
# ) -> User:
#     return await UserService.register_new_user(user)


@auth_router.post("/login")
async def login(
    response: Response,
    webapp_data: WebAppInitData = Depends(get_webapp_data)
) -> Token:
    user = await AuthService.authenticate_user(webapp_data.user.id)
    if not user:
        raise InvalidCredentialsException

    # Сохраняем дату входа
    # await UserService.save_auth_date(webapp_data.user.id, auth_timestamp)

    token = await AuthService.create_token(user.id, webapp_data.user.id)

    response.set_cookie(
        'access_token',
        value=token.access_token,
        max_age=cfg.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=True
    )
    response.set_cookie(
        'refresh_token',
        value=str(token.refresh_token),
        max_age=cfg.REFRESH_TOKEN_EXPIRE_DAYS * 30 * 24 * 60,
        httponly=True,
        secure=True
    )
    return token


@auth_router.post("/swagger_login")
async def swagger_login(
    response: Response,
    tg_id: int,
    secret_key: str
) -> Token:
    user = await AuthService.authenticate_user(tg_id)
    if not user or secret_key != cfg.SECRET_KEY:
        raise InvalidCredentialsException

    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have enough privileges"
        )

    token = await AuthService.create_token(user.id, tg_id)

    response.set_cookie(
        'access_token',
        value=token.access_token,
        max_age=cfg.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=True
    )
    response.set_cookie(
        'refresh_token',
        value=str(token.refresh_token),
        max_age=cfg.REFRESH_TOKEN_EXPIRE_DAYS * 30 * 24 * 60,
        httponly=True,
        secure=True
    )
    return token


@auth_router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    user: UserModel = Depends(get_current_active_user),
):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    await AuthService.logout(request.cookies.get("access_token"))
    return {"message": "Logged out successfully"}


@auth_router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response
) -> Token:
    new_token = await AuthService.refresh_token(
        uuid.UUID(request.cookies.get("refresh_token"))
    )

    response.set_cookie(
        'access_token',
        value=new_token.access_token,
        max_age=cfg.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
    )
    response.set_cookie(
        'refresh_token',
        value=str(new_token.refresh_token),
        max_age=cfg.REFRESH_TOKEN_EXPIRE_DAYS * 30 * 24 * 60,
        httponly=True,
    )
    return new_token


@auth_router.post("/abort")
async def abort_all_sessions(
    response: Response,
    user: Dict[str, Any] = Depends(get_current_user),
):
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')

    await AuthService.abort_all_sessions(uuid.UUID(user.get("user_id")))
    return {"message": "All sessions was aborted"}

