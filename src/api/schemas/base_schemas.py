from typing_extensions import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints

from src.settings import get_settings

cfg = get_settings()


# Валюты
class CurrencyBase(BaseModel):
    code: str
    name: str


class Currency(CurrencyBase):
    id: int

    class Config:
        from_attributes = True