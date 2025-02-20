from aiogram.utils.keyboard import InlineKeyboardBuilder


def payment_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Оплатить 1 ⭐️", pay=True)
    return builder.as_markup()


# def join_keyboard():
#     builder = InlineKeyboardBuilder()
#     builder.button(
#         text=f"Подписаться на канал",
#         url=f"https://t.me/joinchat/AAAAAABf2Yj0-g"
#     )
#     return builder.as_markup()
