import uuid
from datetime import datetime

from typing_extensions import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints, field_validator

from src.settings import get_settings

cfg = get_settings()


def gen_user_id():
    return str(uuid.uuid4())


# Генерация уникального реферального кода из первых 6 символов UUID
def gen_referral_code():
    return str(uuid.uuid4().hex)[:6]


class UserBase(BaseModel):
    username: Optional[str] = Field(None)
    first_name: str
    last_name: Optional[str] = Field(None)
    tg_id: int
    tg_url: Optional[str] = Field(None)
    tg_chat_id: int
    is_bot: bool
    is_premium: Optional[bool] = Field(False)

    level: Optional[int] = Field(0)
    energy: Optional[int] = Field(cfg.energy_limit)
    enterprises_slots: Optional[int] = Field(cfg.enterprises_min_slots)

    total_capacity: Optional[int] = Field(0)
    total_boost_value: Optional[int] = Field(0)

    users_rating_position: Optional[int] = Field(0)
    capacity_rating_position: Optional[int] = Field(0)

    can_open_case: bool = Field(False)

    daily_reward_counter: Optional[int] = Field(0)
    referrals_counter: Optional[int] = Field(None)
    auth_date: Optional[datetime] = Field(None)

    game_balance: Optional[int] = Field(0)

    country_id: Optional[int] = Field(None)
    region_id: Optional[int] = Field(None)
    referrer_id: Optional[uuid.UUID] = None

    is_superuser: bool = Field(False)
    is_verified: bool = Field(False)
    is_active: bool = Field(False)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    tg_url: Optional[str] = Field(None)
    country_id: Optional[int] = Field(None)
    region_id: Optional[int] = Field(None)


class UserBalanceUpdate(BaseModel):
    current_tap_count: int = Field(ge=0, le=500),



class User(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


# Уровни
class LevelBase(BaseModel):
    level: Optional[int] = Field(None)
    capacity_min: Optional[int] = Field(None)
    capacity_max: Optional[int] = Field(None)
    tap_price: Optional[int] = Field(None)
    image_url: Optional[str] = Field(None)
    reward_amount: Optional[int] = Field(None)

    @field_validator('image_url', mode='before')
    def append_image_url(cls, v, values):
        if v is None:
            return cfg.default_image_url
        return f"{cfg.s3_backet_url}{v}"


class Level(LevelBase):
    id: int

    class Config:
        from_attributes = True


# Рейтинг по юзерам
class UserRatingBase(BaseModel):
    user_id: uuid.UUID
    username: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)
    tg_id: Optional[int] = Field(None)
    country_image_url: Optional[str] = Field(None)
    total: int

    @field_validator('country_image_url', mode='before')
    def append_image_url(cls, v, values):
        if v is None:
            return cfg.default_image_url
        return f"{cfg.s3_backet_url}{v}"


class UserRating(UserRatingBase):
    id: int

    class Config:
        from_attributes = True

