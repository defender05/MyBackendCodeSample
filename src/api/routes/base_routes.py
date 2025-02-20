from typing import Any, Union, Dict
from fastapi import APIRouter
from src.core.database import db_helper as db
from api.dao import CurrencyDAO
from api.schemas.base_schemas import Currency
from src.core.schemas import Pagination
from src.settings import get_settings
from loguru import logger as log

cfg = get_settings()

base_router = APIRouter(tags=["Base"], prefix="/base")


@base_router.get("/currencies")
async def get_currencies(
        # offset: Optional[int] = 0,
        # limit: Optional[int] = 25,
) -> list[Currency]:
    """
    Получение валют
    """
    async with db.session_factory() as ses:
        currencies = await CurrencyDAO.find_all(ses)

    return currencies