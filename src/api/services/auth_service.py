import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from src.core.enums import SortType
from src.api.schemas.auth_schemas import RefreshSessionCreate, Token, RefreshSessionUpdate
from src.api.schemas.enterprise_schemas import UserEnterpriseCreate
from src.api.schemas.user_schemas import User, UserCreate, UserUpdate, UserRating
from src.core.models import UserModel, RefreshSessionModel
from src.api.dao import UserDAO, RefreshSessionDAO
from src.core.database import db_helper as db
from src.core.exceptions import InvalidTokenException, TokenExpiredException

from src.api.logging import exception_and_log, log
from src.settings import get_settings

cfg = get_settings()


class AuthService:
    @classmethod
    async def create_token(cls, user_id: uuid.UUID, tg_id: int) -> Token:
        access_token = cls._create_access_token(user_id, tg_id)
        refresh_token_expires = timedelta(
            days=cfg.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = cls._create_refresh_token()

        async with db.session_factory() as ses:
            await RefreshSessionDAO.add(
                ses,
                RefreshSessionCreate(
                    user_id=user_id,
                    refresh_token=refresh_token,
                    expires_in=refresh_token_expires.total_seconds()
                )
            )
            await ses.commit()
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


    @classmethod
    async def logout(cls, token: uuid.UUID) -> None:
        async with db.session_factory() as ses:
            refresh_session = await RefreshSessionDAO.find_one_or_none(
                ses,
                RefreshSessionModel.refresh_token == token
            )
            if refresh_session:
                await RefreshSessionDAO.delete(ses, id=refresh_session.id)
            await ses.commit()


    @classmethod
    async def refresh_token(cls, token: uuid.UUID) -> Token:
        async with db.session_factory() as ses:
            refresh_session = await RefreshSessionDAO.find_one_or_none(
                ses,
                RefreshSessionModel.refresh_token == token
            )

            if refresh_session is None:
                raise InvalidTokenException
            if datetime.now(timezone.utc) >= refresh_session.created_at + timedelta(seconds=refresh_session.expires_in):
                await RefreshSessionDAO.delete(ses, id=refresh_session.id)
                raise TokenExpiredException

            user = await UserDAO.find_one_or_none(ses, id=refresh_session.user_id)
            if user is None:
                raise InvalidTokenException

            access_token = cls._create_access_token(user.id, user.tg_id)
            refresh_token_expires = timedelta(
                days=cfg.REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = cls._create_refresh_token()

            await RefreshSessionDAO.update(
                ses,
                RefreshSessionModel.id == refresh_session.id,
                obj_in=RefreshSessionUpdate(
                    refresh_token=refresh_token,
                    expires_in=refresh_token_expires.total_seconds()
                )
            )
            await ses.commit()
        return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


    @classmethod
    async def authenticate_user(cls, tg_id: int) -> Optional[UserModel]:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_one_or_none(ses, tg_id=tg_id)
        if db_user:
            return db_user
        return None


    @classmethod
    async def abort_all_sessions(cls, user_id: uuid.UUID):
        async with db.session_factory() as ses:
            await RefreshSessionDAO.delete(ses, RefreshSessionModel.user_id == user_id)
            await ses.commit()


    @classmethod
    def _create_access_token(cls, user_id: uuid.UUID, tg_id: int) -> str:
        to_encode = {
            "sub": str(user_id),
            "tg_id": str(tg_id),
            "exp": datetime.utcnow() + timedelta(
                minutes=cfg.ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        encoded_jwt = jwt.encode(
            to_encode, cfg.SECRET_KEY, algorithm=cfg.ALGORITHM)
        return encoded_jwt


    @classmethod
    def _create_refresh_token(cls) -> uuid.UUID:
        return uuid.uuid4()
