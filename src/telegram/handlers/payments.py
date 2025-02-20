import json
from aiogram import Router, types, F
from aiogram.types import Message, PreCheckoutQuery
from src.api.schemas.stars_payment_schemas import StarsPaymentCreate
from src.api.services.stars_payment_service import StarsPaymentService
from loguru import logger as log

payment_router = Router(name=__name__)


# @payment_router.message(F.text == 'test')
# async def test_handler(message: Message):
#     log.info(f"Test message: {message}")
#     await message.answer('Test message')


@payment_router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    log.info(f"Pre_checkout_query: {pre_checkout_query}")
    await pre_checkout_query.answer(ok=True)


@payment_router.message(F.successful_payment)
async def success_payment_handler(message: Message):
    success_pay = message.successful_payment
    # Сохраняем платеж в базу
    order = StarsPaymentCreate(
        tg_id=message.from_user.id,
        id=success_pay.telegram_payment_charge_id,
        currency=success_pay.currency,
        total_amount=success_pay.total_amount,
        invoice_payload=success_pay.invoice_payload,
        provider_payment_charge_id=success_pay.provider_payment_charge_id,
        shipping_option_id=success_pay.shipping_option_id,
        order_info=success_pay.order_info,
    )
    await StarsPaymentService.save_payment(order)
    payload = json.loads(success_pay.invoice_payload)

    # log.info(f"Payload: {payload}")
    log.info(f"Success payment: {success_pay}")
    # Добавляем купленный цифровой товар юзеру
    await StarsPaymentService.buy_product_for_stars(
        success_order=payload
    )
    await message.answer(text="Спасибо за покупку!🥳")


@payment_router.message(F.refunded_payment)
async def refunded_payment_handler(message: Message):
    try:
        refund = message.refunded_payment
        log.success(f"Refunded payment: {refund}")
        await StarsPaymentService.refund_stars(refund.__dict__)
        await message.answer(text="Возврат прошел успешно!")
    except Exception as e:
        log.error(f"Error refunding stars: {e}")
        await message.answer(text="Произошла ошибка при возврате звезд! Попробуйте позже")

