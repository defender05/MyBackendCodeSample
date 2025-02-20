from datetime import datetime
from uuid import UUID

from typing_extensions import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints, field_validator

from src.settings import get_settings

cfg = get_settings()


# Активные объявления на маркете
class MarketBase(BaseModel):
    tg_id: int
    enterprise_id: int


class MarketCreate(MarketBase):
    pass


class Market(MarketBase):
    id: int

    class Config:
        from_attributes = True


# Цены на предприятия, выставленные в маркете
class UserMarketPriceBase(BaseModel):
    market_id: int
    currency_id: int
    price: int


class UserMarketPriceCreate(UserMarketPriceBase):
    pass


class UserMarketPriceUpdate(BaseModel):
    price: int


class UserMarketPrice(UserMarketPriceBase):
    id: int

    class Config:
        from_attributes = True


# История продаж предприятий на маркете
class UserMarketHistoryBase(BaseModel):
    tg_id: int
    enterprise_id: int
    buyer_id: str
    sold_at: Optional[datetime]
    sold_currency_id: int
    sold_price: int


class UserMarketHistoryCreate(BaseModel):
    tg_id: int
    enterprise_id: int
    buyer_id: UUID
    sold_currency_id: int
    sold_price: int


class UserMarketHistory(UserMarketHistoryBase):
    id: int

    class Config:
        from_attributes = True
