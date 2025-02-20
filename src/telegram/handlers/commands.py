import asyncio
import json

from aiogram import Router, types, F
from aiogram.filters import Command, Filter, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (Message, BotCommand, WebAppInfo, LabeledPrice, InlineKeyboardButton)
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.api.services.user_service import UserService
from src.settings import get_settings

from loguru import logger as log

from src.telegram.bot import get_bot
from src.telegram.keyboards.base import payment_keyboard
from telegram.utils import get_all_users

cfg = get_settings()

commands_router = Router(name=__name__)


class Form(StatesGroup):
    post_text = State()


# @commands_router.message(Command("test_pay"))
# async def send_invoice_handler(message: Message):
#     prices = [LabeledPrice(label="XTR", amount=1)]
#     payload = dict(
#         user_id=message.from_user.id,
#         product_type='boost',
#         product_id=1,
#     )
#     await message.answer_invoice(
#         title="Тестовый товар",
#         description="описание",
#         prices=prices,
#         provider_token="",
#         payload=json.dumps(payload),
#         currency="XTR",
#         reply_markup=payment_keyboard(),
#     )


@commands_router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(f"Your ID: {message.from_user.id}")


# Обработка нажатия на инлайн-кнопку
# @commands_router.callback_query(lambda c: c.data == 'button_click')
# async def faq_callback_button(callback_query: types.CallbackQuery):
#     await get_bot().answer_callback_query(callback_query.id)
#     faq_text = (
#         f"какой-то текст..."
#     )
#     await get_bot().send_message(callback_query.from_user.id, faq_text)


@commands_router.message(Command("start"))
async def start_handler(message: Message, command: CommandObject):
    try:
        # Логика для обычного вызова команды /start
        welcome_text = (
            f"Привет, {message.from_user.full_name}! ✌️\n\n"
        )

        builder = InlineKeyboardBuilder()

        webapp_button = InlineKeyboardButton(
            text="Играть",
            web_app=WebAppInfo(url=cfg.webapp_url)
        )
        join_button = InlineKeyboardButton(
            text="Подписаться на канал",
            url="t.me/somechannel",
        )
        faq_button = InlineKeyboardButton(
            text="Как играть",
            callback_data='button_click'
        )
        builder.add(webapp_button)
        builder.add(join_button)
        builder.add(faq_button)
        builder.adjust(1)


        # Логика для обработки deep link
        args = command.args if command else None
        # в данном случае args - это ref_id
        tg_user_id = message.from_user.id
        if args:
            if tg_user_id and tg_user_id != args:
                await UserService.create_or_update_start(message, int(args))
                await message.answer(welcome_text, reply_markup=builder.as_markup())
            else:
                await message.answer("Нельзя пригласить самого себя.")
        else:
            await UserService.create_or_update_start(message, None)
            await message.answer(welcome_text, reply_markup=builder.as_markup())
    except Exception as e:
        log.exception(e)


@commands_router.message(Command("play"))
async def open_webapp(message: Message) -> None:
    welcome_text = "Кликай на кнопку ниже и играй"
    builder = InlineKeyboardBuilder()
    button = InlineKeyboardButton(
        text="Играть",
        web_app=WebAppInfo(url=cfg.webapp_url)
    )
    builder.add(button)

    await message.answer(welcome_text, reply_markup=builder.as_markup())


@commands_router.message(Command("reflink"))
async def get_referral_link(message: Message) -> None:
    reflink = await create_start_link(
        bot=get_bot(),
        payload=str(message.from_user.id),
        encode=False
    )
    await message.answer(f"Ваша пригласительная ссылка: {reflink}")


@commands_router.message((F.text == "/stat") & (F.from_user.id.in_(cfg.bot_admins)))
async def get_stat(message: Message) -> None:
    stat: dict = await UserService.get_bot_stat()
    await message.answer(
        text=(
            "<b>Статистика по пользователям:</b>\n"
            f"Всего: <b>{stat['total_users']}</b>\n"
            f"Всего активных: <b>{stat['active_users']}</b>\n"
            f"Всего заблокированных: <b>{stat['blocked_users']}</b>\n"
            "<b>Динамика</b>:\n"
            f"Прирост за последний день: <b>{stat['new_users_last_day']}</b>\n"
            f"Прирост за последнюю неделю: <b>{stat['new_users_last_week']}</b>\n"
            f"Прирост за последний месяц: <b>{stat['new_users_last_month']}</b>\n"
        )
    )


@commands_router.message(Command("support"))
async def support_handler(message: Message):
    await message.answer(
        text="@somechannel"
    )


@commands_router.message((F.text == "/new_post") & (F.from_user.id.in_(cfg.bot_admins)))
async def new_post(message: Message, state: FSMContext):
    await state.set_state(Form.post_text)
    await message.answer(
        f'Введите текст поста:'
    )


@commands_router.message((F.text == "/cancel") & (F.from_user.id.in_(cfg.bot_admins)))
async def cancel(message: Message, state: FSMContext):  # Отмена формы
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer(
        "Cancelled.",
    )


@commands_router.message(Form.post_text)
async def post_text(message: Message, state: FSMContext):
    """
    Send post to all users
    """
    # Получаем список всех юзеров с базы
    db_users = await get_all_users(limit=500)

    await state.clear()

    # Проверяем наличие инлайн кнопок в исходном сообщении
    inline_keyboard = message.reply_markup if message.reply_markup else None

    # Отправляем пост всем полученным юзерам
    for user in db_users:
        try:
            await message.send_copy(chat_id=user.tg_chat_id, reply_markup=inline_keyboard)
            # Чтобы не превышать лимиты телеги, делаем задержку
            await asyncio.sleep(0.2)  # 5 сообщений в сек
        except Exception as e:
            log.error(f"Error sending message to {user.tg_chat_id}: {e}")
