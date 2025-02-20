from typing import Optional

from pydantic import BaseModel, Field


# class TelegramUser(BaseModel):
#     id: int
#     is_bot: Optional[bool] = Field(default=None)
#     first_name: str
#     last_name: Optional[str] = Field(default=None)
#     username: Optional[str] = Field(default=None)
#     language_code: str
#     is_premium: bool
#     added_to_attachment_menu: Optional[bool] = Field(default=None)
#     allows_write_to_pm: bool
#     photo_url: Optional[str] = Field(default=None)


class Pagination(BaseModel):
    offset: int = Field(default=0)
    limit: int = Field(default=100, gt=0, le=200)


class StarsTransactionPagination(BaseModel):
    offset: int = Field(default=0)
    limit: int = Field(default=100, gt=0, le=100)


class Timeout(BaseModel):
    req_timeout: int = Field(default=100, ge=10)
