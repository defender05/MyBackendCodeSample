import decimal
import uuid

from typing_extensions import Annotated, Optional
from pydantic import BaseModel, Field, StringConstraints


class UserReferralBase(BaseModel):
    owner_id: uuid.UUID
    referral_id: uuid.UUID
    level_id: int = 1


class UserReferralCreate(UserReferralBase):
    pass


class UserReferralUpdate(BaseModel):
    pass


class UserReferral(UserReferralBase):
    id: int

    class Config:
        from_attributes = True
