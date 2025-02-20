from aiogram import Bot
from aiogram.types import Message, LabeledPrice, StarTransactions, StarTransaction
from src.api.schemas.stars_payment_schemas import StarsInvoiceLinkCreate
from src.settings import get_settings

cfg = get_settings()


# Создаем ссылку для оплаты в stars
async def create_stars_payment_link(bot: Bot, pay_link: StarsInvoiceLinkCreate) -> str:
    link = await bot.create_invoice_link(
        title=pay_link.title,
        description=pay_link.description,
        payload=pay_link.payload,  # не видно пользователям
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label='XTR', amount=pay_link.price_amount)],
        # suggested_tip_amounts=[5, 10, 50],
        photo_url=pay_link.photo_url,
    )
    return link


async def stars_transactions(
        bot,
        offset: int,
        limit: int,
        request_timeout: int,
) -> list[StarTransaction]:
    return await bot.get_star_transactions(
        offset=offset,
        limit=limit,
        request_timeout=request_timeout
    )




