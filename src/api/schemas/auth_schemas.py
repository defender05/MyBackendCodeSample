import uuid
from typing_extensions import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints

from src.settings import get_settings

cfg = get_settings()


class RefreshSessionCreate(BaseModel):
    refresh_token: uuid.UUID
    expires_in: int
    user_id: uuid.UUID


class RefreshSessionUpdate(RefreshSessionCreate):
    user_id: Optional[uuid.UUID] = Field(None)


class Token(BaseModel):
    access_token: str
    refresh_token: uuid.UUID
    token_type: str



