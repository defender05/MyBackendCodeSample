import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field



# GENERATE PAY LINK
class StarsInvoiceLinkBase(BaseModel):
    title: str
    description: str
    payload: str
    price_amount: int
    photo_url: Optional[str] = Field(None)


class StarsInvoiceLinkCreate(StarsInvoiceLinkBase):
    pass


class StarsInvoiceLink(StarsInvoiceLinkBase):

    class Config:
        from_attributes = True


# SUCCESS PAYMENT
class StarsPaymentBase(BaseModel):
    tg_id: int

    id: str  # Unique identifier of the transaction
    currency: str = Field(default='XTR')
    total_amount: int
    invoice_payload: str
    provider_payment_charge_id: str
    shipping_option_id: Optional[str] = Field(None)
    order_info: Optional[dict[str, Any]] = Field(None)


class StarsPaymentCreate(StarsPaymentBase):
    pass


class StarsPayment(StarsPaymentBase):

    class Config:
        from_attributes = True


# REFUNDS
class StarsRefundBase(BaseModel):
    tg_id: int

    id: str  # Unique identifier of the transaction
    currency: str = Field(default='XTR')
    total_amount: int
    invoice_payload: str
    provider_payment_charge_id: str


class StarsRefundCreate(StarsPaymentBase):
    pass


class StarsRefund(StarsPaymentBase):
    class Config:
        from_attributes = True
