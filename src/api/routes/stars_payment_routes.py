from typing import Any, Dict

from fastapi import APIRouter, Depends

# from src.core.queque import get_broker, get_stream, get_config
from src.core.dependencies import get_current_user, get_current_superuser
# from src.core.schemas import StarsTransactionPagination, Timeout
from src.api.schemas.stars_payment_schemas import StarsInvoiceLinkCreate
from src.api.schemas.user_schemas import User
from src.api.tg_payment import create_stars_payment_link

from src.settings import get_settings

cfg = get_settings()
# broker = get_broker()

if cfg.run_type != 'local':
    from src.telegram.bot import get_bot

stars_payment_router = APIRouter(prefix='/stars_payment', tags=["Stars payment"])


# @broker.subscriber(stream='telegram_invoice_link', subject='invoice_link_output')
@stars_payment_router.post("/getInvoiceLink")
async def get_invoice_link(
        link: StarsInvoiceLinkCreate = Depends(StarsInvoiceLinkCreate),
        user: Dict[str, Any] = Depends(get_current_user),
) -> str:
    """
    Возвращает ссылку для оплаты цифрового товара в telegram stars\n
    Источник: https://core.telegram.org/bots/api#createinvoicelink\n

    В payload нужно передать строку, полученную из словаря,  \n
    user_id - telegram id пользователя\n
    product_type - тип товара \n
    product_id - идентификатор товара\n
    """
    pay_link = await create_stars_payment_link(get_bot(), link)
    return pay_link


@stars_payment_router.post("/makeRefund")
async def make_refund(
        transaction_id: str,
        user: Dict[str, Any] = Depends(get_current_superuser),
) -> Any:
    """
    Делаем рефанд потраченных старс обратно на счет пользователю\n
    """
    refund = await get_bot().refund_star_payment(
        user_id=user.get("tg_id"),
        telegram_payment_charge_id=transaction_id,
        request_timeout=1000
    )
    return refund

# @star_order_router.post("/saveTransaction/{transaction_id}")
# async def save_stars_transaction(
#         order: StarsOrderCreate = Depends(StarsOrderCreate)
# ) -> StarsOrder:
#     """
#     Сохраняет транзакцию telegram stars в базу
#     """
#     trans = await StarsOrderService.create_order()
#     return trans


# @stars_payment_router.get("/listStarsTransactions")
# async def get_stars_transactions(
#         pag: StarsTransactionPagination = Depends(StarsTransactionPagination),
#         tr: Timeout = Depends(Timeout),
#         user: User = Depends(get_current_user),
# ):
#     """
#     Получение списка транзакций пользователя в telegram stars\n
#     req_timeout - время ожидания ответа в секундах
#     """
#     transactions = await stars_transactions(
#         bot=get_bot(),
#         offset=pag.offset,
#         limit=pag.limit,
#         request_timeout=tr.req_timeout,
#     )
#     return transactions
