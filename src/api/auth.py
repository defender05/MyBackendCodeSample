import time
from datetime import datetime
from typing import Optional, Dict, cast, Any

from fastapi import HTTPException, Request, status, Cookie
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.security import HTTPAuthorizationCredentials, OAuth2, OAuth2AuthorizationCodeBearer
from fastapi.security.http import HTTPBase

from aiogram.utils.web_app import safe_parse_webapp_init_data, WebAppUser, WebAppInitData
from src.api.services.user_service import UserService
from src.settings import get_settings
from loguru import logger as log

cfg = get_settings()


class OAuth2BearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        refreshUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(
            clientCredentials=cast(
                Any,
                {
                    "tokenUrl": tokenUrl,
                    "refreshUrl": refreshUrl,
                    "scopes": scopes,
                },
            )
        )
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        token: str = request.headers.get("Authorization")
        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return token


tg_auth_schema = HTTPBase(scheme="bearer")
oauth2_scheme = OAuth2BearerWithCookie(
    tokenUrl="/api/v1/auth/swagger_login",
    refreshUrl="/api/v1/auth/refresh"
)


async def verify_init_data(
        auth_cred: HTTPAuthorizationCredentials
) -> WebAppInitData:
    try:
        data: WebAppInitData = safe_parse_webapp_init_data(
            token=cfg.bot_token,
            init_data=str(auth_cred.credentials),
        )
        # Создаем пользователя в базе, если его нет
        await UserService.create_or_update_webapp(
            user=data.user,
            ref_id=int(data.start_param) if data.start_param else None,
        )
        return data
    except ValueError as er:
        cfg.debug and log.debug(f'verify_init_data error: {er}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webapp init data"
        )




