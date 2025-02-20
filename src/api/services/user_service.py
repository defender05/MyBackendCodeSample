from datetime import datetime, timedelta
import string
import time
import random
import uuid

from typing import Optional, Any, Dict

from aiogram.enums import ChatMemberStatus
from aiogram.utils.web_app import WebAppUser
from fastapi import HTTPException, status
from sqlalchemy import select, func, text, desc, and_, cast, Date
from sqlalchemy.orm import joinedload

from src.core.enums import SortType
from src.api.schemas.country_schemas import CountryBase
from src.api.schemas.enterprise_schemas import UserEnterpriseCreate
from src.api.schemas.user_schemas import User, UserCreate, UserUpdate, UserRating, \
    UserDailyRewardedTaskCreate, UserReferralRewardsCreate, Level, LevelBase, UserRewardedTaskCreate
from src.api.schemas.user_referral_schemas import UserReferralCreate
from src.core.models import UserModel, ReferralModel, UserEnterpriseModel, \
    GdpUserRatingModel, CapacityUserRatingModel, UserBoostModel
from src.api.dao import UserDAO, UserReferralDAO, UserEnterpriseDAO, EnterpriseDAO, CountryDAO, RegionDAO, \
    GdpUserRatingDAO, CapacityUserRatingDAO, RewardedTaskDAO, UserRewardedTaskDAO, LevelDAO, \
    DailyRewardsDAO, UserDailyRewardedTaskDAO, UserReferralRewardsDAO, ReferralRewardsDAO, UserLevelRewardsDAO
from src.core.database import db_helper as db

from src.api.logging import log
from src.settings import get_settings

cfg = get_settings()

if cfg.run_type != 'local':
    from telegram.bot import get_bot


def generate_unique_id() -> str:
    epoch_ms = int(time.time())
    random_int = random.randint(1000, 9999)
    return f"{epoch_ms}.{random_int}"


def generate_referral_code(length=6):
    characters = string.ascii_uppercase + string.digits
    referral_code = ''.join(random.choice(characters) for _ in range(length))
    return referral_code


class UserService:
    @classmethod
    async def check_user(cls, user_id: str) -> User | str:
        async with db.session_factory() as session:
            user_exist = await UserDAO.find_one_or_none(session, id=user_id)
            if user_exist:
                return user_exist
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail='User not found')


    @classmethod
    async def check_user_by_telegram_id(cls, tg_id: int) -> User | None:
        async with db.session_factory() as session:
            user_exist = await UserDAO.find_one_or_none(session, tg_id=tg_id)
            if user_exist is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
            return user_exist



    @classmethod
    async def create_user(cls, user: UserCreate) -> Optional[User]:
        async with db.session_factory() as ses:
            user_exist = await UserDAO.find_one_or_none(ses, tg_id=user.tg_id)
            owner = await UserDAO.find_one_or_none(ses, tg_id=user.referrer_id)
            if user_exist is None:
                if owner is None:
                    user.referrer_id = None
                else:
                    user.referrer_id = owner.id

                db_user = await UserDAO.add(ses, user)
                total_capacity = 0

                for i in range(1, 4):  # Добавляем 3 начальных предприятия юзеру
                    await UserEnterpriseDAO.add(
                        ses,
                        UserEnterpriseCreate(
                            tg_id=user.tg_id,
                            enterprise_id=i,
                        )
                    )
                    current_ent = await EnterpriseDAO.find_one_or_none(ses, id=i)
                    total_capacity += current_ent.capacity
                    await ses.commit()

                db_user.total_capacity = total_capacity
                await ses.commit()

                if owner:
                    log.info(f'Owner:{owner}')
                    level = 1
                    current_referrer_id = owner.referrer_id

                    # Реализация многоуровневой реферальной системы
                    # Идем вверх по цепочке, пока не достигнем 10 уровня или юзера, которого никто не приглашал
                    while level <= 10:

                        # если такой юзер найден, добавляем одну запись и выходим из цикла
                        if current_referrer_id is None:
                            ref_obj = UserReferralCreate(
                                owner_id=owner.id,
                                referral_id=db_user.id,
                                level_id=1
                            )
                            log.success(f'Юзер найден. Добавляем одну запись:{ref_obj}')
                            await UserReferralDAO.add(ses, obj_in=ref_obj)
                            await ses.commit()
                            break
                        else:   # если нет, добавляем записи (рефералов) для каждого юзера вверх по цепочке
                            log.warning(f'Юзер не найден. Идем вверх по цепочке')
                            next_owner = await UserDAO.find_one_or_none(ses, id=current_referrer_id)
                            if next_owner is None:
                                log.warning(f'Next owner не найден')
                                break

                            level += 1
                            ref_for_next_owner = UserReferralCreate(
                                owner_id=next_owner.id,
                                referral_id=db_user.id,
                                level_id=level
                            )
                            await UserReferralDAO.add(ses, obj_in=ref_for_next_owner)
                            await ses.commit()
                            current_referrer_id = next_owner.referrer_id
                    else:
                        log.warning(f"Owner by uuid: {user.referrer_id} not found")


                return db_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with tg_id:{user.tg_id} already exists"
                )


    @classmethod
    async def get_users(
            cls,
            *query_filter,
            offset: Optional[int] = 0,
            limit: Optional[int] = 100,
            order_by: Optional[str] = 'id',
            sort_type: str = SortType.ASC,
            **filter_by,
    ) -> list[User]:
        async with db.session_factory() as session:
            users = await UserDAO.find_all(
                session,
                *query_filter,
                offset=offset,
                limit=limit,
                order_by=order_by,
                sort_type=sort_type,
                **filter_by,
            )
            if users is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Users not found"
                )
            return [db_user for db_user in users]


    @classmethod
    async def get_user_by_id(
            cls,
            user_id: uuid.UUID
    ) -> Any:
        async with db.session_factory() as session:
            db_user = await UserDAO.find_first(session, id=user_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )
            return db_user


    @classmethod
    async def get_user_by_telegram_id(
            cls,
            tg_id: int,
    ) -> dict[str, Any]:
        async with (db.session_factory() as ses):
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            country_data = await CountryDAO.find_first(ses, id=db_user.country_id)
            country = CountryBase(**country_data.to_dict()) if country_data else None
            region = await RegionDAO.find_first(ses, id=db_user.region_id)
            level_data = await LevelDAO.find_first(ses, id=db_user.level)
            level = LevelBase(**level_data.to_dict()) if level_data else None
            # user_boosts = await UserBoostDAO.find_all(ses, tg_id=tg_id)

            # Получаем список бустов юзера
            boost_stmt = (
                select(UserBoostModel)
                .where(UserBoostModel.tg_id == db_user.tg_id)
                .options(joinedload(UserBoostModel.boost))
            )
            results = await ses.execute(boost_stmt)
            user_boosts = [{'created_at': boost.created_at, 'boost_info': boost.boost.to_dict()} for boost in results.scalars().all()]

            user_rating_gdp = await GdpUserRatingDAO.find_first(ses, user_id=db_user.id)
            user_rating_capacity = await CapacityUserRatingDAO.find_first(ses, user_id=db_user.id)

            gdp_rating_position = user_rating_gdp.position if user_rating_gdp else None
            capacity_rating_position = user_rating_capacity.position if user_rating_capacity else None

            output_dict = {
                'id': str(db_user.id),
                'tg_id': db_user.tg_id,
                'username': db_user.username,
                'first_name': db_user.first_name,
                'last_name': db_user.last_name,
                'level': level.dict() if level else None,
                'country': country.dict() if country else None,
                'region': region.to_dict() if region else None,
                'total_capacity': db_user.total_capacity,
                'boosts': user_boosts if user_boosts else None,
                'total_boost_value': db_user.total_boost_value,
                'user_rating_position': gdp_rating_position,
                'capacity_rating_position': capacity_rating_position,
                'energy': db_user.energy,
                'game_balance': db_user.game_balance,
                'enterprises_slots': db_user.enterprises_slots,
                'can_open_case': db_user.can_open_case,
                'referrer_id': str(db_user.referrer_id),
                'auth_date': db_user.auth_date,
                'daily_reward_counter': db_user.daily_reward_counter,
                'referrals_counter': db_user.referrals_counter
            }

            return output_dict



    @classmethod
    async def update_user_by_uuid(
            cls,
            tg_id: int,
            user_update: UserUpdate,
    ) -> UserUpdate:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            if user_update.username is not None:
                db_user.username = user_update.username
            if user_update.first_name is not None:
                db_user.first_name = user_update.first_name
            if user_update.last_name is not None:
                db_user.last_name = user_update.last_name
            if user_update.enterprises_slots is not None:
                db_user.enterprises_slots = user_update.enterprises_slots

            await ses.commit()
            return user_update


    @classmethod
    async def update_user_by_telegram_id(
            cls,
            tg_id: int,
            user_update: UserUpdate,
    ) -> Any:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            output_dict = {}

            # if user_update.username is not None:
            #     db_user.username = user_update.username
            #     output_dict['username'] = db_user.username
            if user_update.first_name is not None:
                db_user.first_name = user_update.first_name
                output_dict['first_name'] = db_user.first_name
            if user_update.last_name is not None:
                db_user.last_name = user_update.last_name
                output_dict['last_name'] = db_user.last_name
            if user_update.tg_url is not None:
                db_user.tg_url = user_update.tg_url
                output_dict['tg_url'] = db_user.tg_url
            if user_update.country_id is not None:
                if db_user.country_id is None and user_update.country_id == 1 and user_update.region_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"You cannot the set country_id=1 while the region_id is None"
                    )

                country = await CountryDAO.find_first(ses, id=user_update.country_id)
                if country is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Country_id {user_update.country_id} not found"
                    )

                if user_update.country_id != db_user.country_id:
                    db_user.game_balance = int(db_user.game_balance / 2)

                db_user.country_id = user_update.country_id
                db_user.region_id = None

                output_dict['country'] = dict(
                    id=country.id,
                    name=country.name,
                    description=country.description,
                    image_url=country.image_url,
                    total_gdp=country.total_gdp,
                )

            if user_update.region_id is not None:
                if db_user.country_id is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"You cannot update the region_id while the country_id is None"
                    )

                region = await RegionDAO.find_first(
                    ses,
                    id=user_update.region_id,
                    country_id=db_user.country_id
                )
                if region is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Region from country_id {user_update.country_id} not found"
                    )

                if user_update.country_id is None and db_user.country_id == 1 and user_update.region_id != db_user.region_id:
                    db_user.game_balance = int(db_user.game_balance / 2)

                db_user.region_id = user_update.region_id

                output_dict['region'] = dict(
                    id=region.id,
                    name=region.name,
                    country_id=region.country_id,
                )

            await ses.commit()
            return output_dict



    @classmethod
    async def update_game_balance(
            cls,
            tg_id: int,
            new_tap_count: int,
    ) -> dict:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            if db_user.energy == 0:
                return dict(
                    message="The energy is gone",
                    balance=db_user.game_balance
                )

            if new_tap_count is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"current_tap_count is required"
                )

            current_tap_count = (cfg.energy_limit - db_user.energy)

            if new_tap_count < current_tap_count or new_tap_count < 0:
                return dict(
                    message="""Вы не можете передать кол-во кликов меньше 0 или меньше,
                     чем уже сделали за сегодня""",
                    balance=db_user.game_balance
                )

            if new_tap_count == 0:
                return dict(
                    message="Make taps before update your balance",
                    balance=db_user.game_balance
                )

            new_tap_count = new_tap_count - current_tap_count

            # total_boost = db_user.total_boost_value if db_user.total_boost_value != 0 else 1
            # composition = total_boost * db_user.total_capacity
            # additional_value = composition / 100 if composition != 0 else 0
            level = await LevelDAO.find_first(ses, level=db_user.level)
            tap_price = level.tap_price

            if level is None or level.tap_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Level not found or tap_price is empty"
                )

            if db_user.energy >= new_tap_count:
                db_user.game_balance += tap_price * new_tap_count
                db_user.energy -= new_tap_count
                await ses.commit()
                return dict(
                    message="Balance successfully updated",
                    balance=db_user.game_balance
                )
            else:
                db_user.game_balance += tap_price * db_user.energy
                db_user.energy = 0
                await ses.commit()
                return dict(
                    message="Balance successfully updated",
                    balance=db_user.game_balance
                )


    @classmethod
    async def buy_slot(
            cls,
            tg_id: int,
    ) -> dict[str, Any]:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            if db_user.enterprises_slots > cfg.enterprises_max_slots:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Количество слотов уже достигло своего максимума"
                )

            db_user.enterprises_slots += 1
            await ses.commit()
            return dict(
                message="Слот успешно добавлен",
                number_of_slots=db_user.enterprises_slots
            )


    @classmethod
    async def get_referral_stats(
            cls,
            tg_id: int,
    ) -> dict[str, Any]:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            stmt = (
                select(ReferralModel.level_id, func.count(ReferralModel.id))
                .filter(ReferralModel.owner_id == db_user.id)
                .group_by(ReferralModel.level_id)
            )
            res = await ses.execute(stmt)
            refferal_counts = res.all()
            if refferal_counts is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Referrals not found"
                )

            referral_stats = {item[0]: item[1] for item in refferal_counts}
            return dict(
                total_referrals=sum(referral_stats.values()),
                level_stats=referral_stats
            )


    @classmethod
    async def create_or_update_webapp(
            cls,
            user: WebAppUser,
            ref_id: Optional[int]
    ):
        if user is None:
            return

        async with db.session_factory() as ses:
            try:
                tg_user_id = user.id
                username = user.username

                exist_user = await UserDAO.find_one_or_none(ses, tg_id=tg_user_id)
                owner_user = None

                if ref_id:
                    owner_user = await UserDAO.find_one_or_none(ses, tg_id=ref_id)

                if exist_user is None:
                    cfg.debug and log.info(f'Пользователь {tg_user_id} не найден. Создание...')

                    user_obj = UserCreate(
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        tg_id=tg_user_id,
                        tg_url=f'https://t.me/{username}' if username else None,
                        tg_chat_id=tg_user_id,
                        is_bot=user.is_bot if user.is_bot else False,
                        is_premium=user.is_premium,
                        level=1,
                        energy=cfg.energy_limit,
                        enterprises_slots=cfg.enterprises_min_slots,
                        total_capacity=0,
                        total_boost_value=0,
                        users_rating_position=0,
                        capacity_rating_position=0,
                        can_open_case=False,
                        daily_reward_counter=0,
                        referrals_counter=0,
                        game_balance=0,
                        is_superuser=False,
                        is_verified=False,
                        is_active=True,
                        referrer_id=str(owner_user.id) if owner_user else None
                    )
                    new_user = await UserDAO.add(
                        ses,
                        user_obj
                    )

                    total_capacity = 0

                    # Добавляем 1 начальное предприятие юзеру
                    await UserEnterpriseDAO.add(
                        ses,
                        UserEnterpriseCreate(
                            tg_id=new_user.tg_id,
                            enterprise_id=1,
                        )
                    )
                    current_ent = await EnterpriseDAO.find_one_or_none(ses, id=1)
                    total_capacity += current_ent.capacity
                    new_user.total_capacity = total_capacity
                    await ses.commit()

                    if owner_user:
                        level = 1
                        current_referrer_id = owner_user.referrer_id

                        owner_user.referrals_counter += 1

                        # Добавялем запись овнеру о выполненном задании на кол-во рефералов
                        if owner_user.referrals_counter:
                            reward = await ReferralRewardsDAO.find_first(
                                ses,
                                ref_count=owner_user.referrals_counter
                            )
                            if reward and reward.amount and reward.ref_count == owner_user.referrals_counter:
                                exist_task = await UserReferralRewardsDAO.find_first(
                                    ses, tg_id=owner_user.tg_id, reward_id=reward.id)
                                if exist_task is None:
                                    await UserReferralRewardsDAO.add(
                                        ses,
                                        UserReferralRewardsCreate(
                                            tg_id=owner_user.tg_id,
                                            reward_id=reward.id,
                                            is_claimed=False,
                                        )
                                    )

                        # Реализация многоуровневой реферальной системы
                        # Идем вверх по цепочке, пока не достигнем 10 уровня или юзера, которого никто не приглашал
                        while level <= 10:

                            # если такой юзер найден, добавляем одну запись и выходим из цикла
                            if current_referrer_id is None:
                                ref_obj = UserReferralCreate(
                                    owner_id=owner_user.id,
                                    referral_id=new_user.id,
                                    level_id=1
                                )
                                await UserReferralDAO.add(ses, obj_in=ref_obj)
                                await ses.commit()
                                break
                            else:  # если нет, добавляем записи (рефералов) для каждого юзера вверх по цепочке
                                next_owner = await UserDAO.find_one_or_none(ses, id=current_referrer_id)
                                if next_owner is None:
                                    break

                                level += 1
                                ref_for_next_owner = UserReferralCreate(
                                    owner_id=next_owner.id,
                                    referral_id=new_user.id,
                                    level_id=level
                                )
                                await UserReferralDAO.add(ses, obj_in=ref_for_next_owner)
                                await ses.commit()
                                current_referrer_id = next_owner.referrer_id
 

                    if new_user is not None:
                        await ses.commit()
                        cfg.debug and log.success(f'Новый пользователь успешно создан: {new_user}')
                    else:
                        cfg.debug and log.error(f'Ошибка создания пользователя:  {exist_user}')

                else:
                    log.info(f'Пользователь уже создан: \n{exist_user}\nОбновление данных пользователя...')
                    update_obj = UserUpdate(
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        tg_url=f'https://t.me/{user.username}' if user.username else None,
                    )
                    updated_user = await cls._auto_update_user(
                        session=ses,
                        current_user=exist_user,
                        user_update=update_obj,
                    )
                    cfg.debug and log.success(f'Пользователь успешно обновлен: {updated_user}')

            except Exception as e:
                cfg.debug and log.error(f'Ошибка при создании или обновлении пользователя: {e}')



    @classmethod
    async def create_or_update_start(cls, message, ref_id: Optional[int]):
        if message is None:
            return

        async with db.session_factory() as ses:
            try:
                tg_user_id = message.from_user.id

                exist_user = await UserDAO.find_one_or_none(ses, tg_id=tg_user_id)
                owner_user = None

                if ref_id:
                    owner_user = await UserDAO.find_one_or_none(ses, tg_id=ref_id)

                if exist_user is None:
                    cfg.debug and log.info(f'Пользователь {message.from_user.id} не найден. Создание...')

                    user_obj = UserCreate(
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name,
                        tg_id=message.from_user.id,
                        tg_url=f'https://t.me/{message.from_user.username}' if message.from_user.username else None,
                        tg_chat_id=message.chat.id,
                        is_bot=message.from_user.is_bot,
                        is_premium=message.from_user.is_premium,
                        level=1,
                        energy=cfg.energy_limit,
                        enterprises_slots=cfg.enterprises_min_slots,
                        total_capacity=0,
                        total_boost_value=0,
                        users_rating_position=0,
                        capacity_rating_position=0,
                        can_open_case=False,
                        daily_reward_counter=0,
                        referrals_counter=0,
                        game_balance=0,
                        is_superuser=False,
                        is_verified=False,
                        is_active=True,
                        referrer_id=str(owner_user.id) if owner_user else None
                    )
                    new_user = await UserDAO.add(
                        ses,
                        user_obj
                    )

                    total_capacity = 0

                    # Добавляем 1 начальное предприятие юзеру
                    await UserEnterpriseDAO.add(
                        ses,
                        UserEnterpriseCreate(
                            tg_id=new_user.tg_id,
                            enterprise_id=1,
                        )
                    )
                    current_ent = await EnterpriseDAO.find_one_or_none(ses, id=1)
                    total_capacity += current_ent.capacity
                    new_user.total_capacity = total_capacity
                    await ses.commit()

                    if owner_user:
                        level = 1
                        current_referrer_id = owner_user.referrer_id

                        owner_user.referrals_counter += 1

                        # Добавялем запись овнеру о выполненном задании на кол-во рефералов
                        if owner_user.referrals_counter:
                            reward = await ReferralRewardsDAO.find_first(
                                ses,
                                ref_count=owner_user.referrals_counter
                            )
                            if reward and reward.amount:
                                exist_task = await UserReferralRewardsDAO.find_first(
                                    ses, tg_id=owner_user.tg_id, reward_id=reward.id)
                                if exist_task is None:
                                    await UserReferralRewardsDAO.add(
                                        ses,
                                        UserReferralRewardsCreate(
                                            tg_id=owner_user.tg_id,
                                            reward_id=reward.id,
                                            is_claimed=False,
                                        )
                                    )

                        # Реализация многоуровневой реферальной системы
                        # Идем вверх по цепочке, пока не достигнем 10 уровня или юзера, которого никто не приглашал
                        while level <= 10:

                            # если такой юзер найден, добавляем одну запись и выходим из цикла
                            if current_referrer_id is None:
                                ref_obj = UserReferralCreate(
                                    owner_id=owner_user.id,
                                    referral_id=new_user.id,
                                    level_id=1
                                )
                                cfg.debug and log.success(f'Юзер найден. Добавляем одну запись:{ref_obj}')
                                await UserReferralDAO.add(ses, obj_in=ref_obj)
                                await ses.commit()
                                break
                            else:  # если нет, добавляем записи (рефералов) для каждого юзера вверх по цепочке
                                cfg.debug and log.warning(f'Юзер не найден. Идем вверх по цепочке')
                                next_owner = await UserDAO.find_one_or_none(ses, id=current_referrer_id)
                                if next_owner is None:
                                    log.warning(f'Next owner не найден')
                                    break

                                level += 1
                                ref_for_next_owner = UserReferralCreate(
                                    owner_id=next_owner.id,
                                    referral_id=new_user.id,
                                    level_id=level
                                )
                                await UserReferralDAO.add(ses, obj_in=ref_for_next_owner)
                                await ses.commit()
                                current_referrer_id = next_owner.referrer_id
                        else:
                            cfg.debug and log.warning(f"Owner by uuid: {owner_user.referrer_id} not found")

                    if new_user is not None:
                        await ses.commit()

                        cfg.debug and log.success(f'Новый пользователь успешно создан: {new_user}')
                    else:
                        cfg.debug and log.error(f'Ошибка создания пользователя:  {exist_user}')

                else:
                    log.info(f'Пользователь уже создан: \n{exist_user}\nОбновление данных пользователя...')
                    user_obj = UserUpdate(
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name,
                        tg_url=f'https://t.me/{message.from_user.username}' if message.from_user.username else None,
                    )
                    updated_user = await cls._auto_update_user(
                        session=ses,
                        current_user=exist_user,
                        user_update=user_obj,
                    )
                    cfg.debug and log.success(f'Пользователь успешно обновлен: {updated_user}')

            except Exception as e:
                if cfg.debug:
                    log.error(f'Ошибка при создании или обновлении пользователя: {e}')
                else:
                    log.error(f'Ошибка при создании или обновлении пользователя')


    @classmethod
    async def _auto_update_user(
            cls,
            session,
            current_user: User,
            user_update: UserUpdate
    ) -> UserUpdate:

        if user_update.username is not None:
            current_user.username = user_update.username
        if user_update.first_name is not None:
            current_user.first_name = user_update.first_name
        if user_update.last_name is not None:
            current_user.last_name = user_update.last_name
        if user_update.tg_url is not None:
            current_user.tg_url = user_update.tg_url

        await session.commit()
        return user_update


    @classmethod
    async def get_users_rating_by_region(
            cls,
            region_id: int,
            offset: int = 0,
            limit: int = 100,
    ) -> list[Dict[str, Any]]:
        async with db.session_factory() as ses:
            stmt = (
                select(UserModel)
                .filter(and_(UserModel.region_id != None, UserModel.region_id == region_id))
                .filter(UserModel.game_balance != None)
                .offset(offset)
                .limit(limit)
                .order_by(desc(text('game_balance')))
            )

            result = await ses.execute(stmt)
            users = result.scalars().all()

            if users is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Users gdp rating not found"
                )
                
            return [
                {
                    'id':user.id,
                    'first_name':user.first_name,
                    'last_name':user.last_name,
                    'gdp':user.game_balance,
                    'capacity':user.total_capacity
                } 
                for user in users
            ]



    @classmethod
    async def get_referral_rewards(
            cls,
            tg_id: int,
            offset: int = 0,
            limit: int = 100,
    ) -> list[dict[str, Any]]:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            referral_rewards = await ReferralRewardsDAO.find_all(ses, offset=offset, limit=limit)
            if not referral_rewards:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Referrals rewards not found"
                )

            user_tasks = await UserReferralRewardsDAO.find_all(
                ses, tg_id=db_user.tg_id, offset=offset, limit=limit
            )

            # Преобразуем список выполненных заданий в множество для быстрого поиска
            completed_task_ids = {user_task.reward_id for user_task in user_tasks}
            claimed_task_ids = {user_task.reward_id for user_task in user_tasks if user_task.is_claimed}

            out = []
            for task in referral_rewards:
                item = {
                    'id': task.id,
                    'is_completed': task.id in completed_task_ids,  # Проверка, выполнено ли задание
                    'is_claimed': task.id in claimed_task_ids,
                    'ref_count': task.ref_count,
                    'amount': task.amount,
                }
                out.append(item)
            return out

            # return [task for task in referral_reward]



    @classmethod
    async def claim_referrals_reward(
            cls,
            tg_id: int,
            ref_count: int,
    ) -> Any:
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            if db_user.referrals_counter is None or db_user.referrals_counter < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"The user has no referrals"
                )

            reward = await ReferralRewardsDAO.find_one_or_none(
                ses,
                ref_count=ref_count
            )
            if reward is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Referral reward not found"
                )

            exist_task = await UserReferralRewardsDAO.find_first(
                ses,
                tg_id=db_user.tg_id,
                reward_id=reward.id
            )

            if exist_task is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This task has not been completed"
                )

            if exist_task and exist_task.is_claimed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"This reward already claimed"
                )

            # if reward.ref_count != db_user.referrals_counter:
            #     raise HTTPException(
            #         status_code=status.HTTP_400_BAD_REQUEST,
            #         detail=f"There are no rewards available"
            #     )

            db_user.game_balance += reward.amount
            exist_task.is_claimed = True
            await ses.commit()

            return dict(
                user_task=exist_task.to_dict(),
                reward=reward.to_dict(),
            )



    @classmethod
    async def update_user_from_superuser(
            cls,
            user,
            user_upd: UserUpdate
    ) -> User:
        async with db.session_factory() as session:
            user_update = await UserDAO.update(
                session,
                UserModel.id == user.id,
                obj_in=user_upd)

            await session.commit()
            return user_update

    @classmethod
    async def delete_user_from_superuser(
            cls,
            user,
    ):
        async with db.session_factory() as session:
            try:
                await UserDAO.delete(session, UserModel.id == user.id)
                await session.commit()
            except Exception as e:
                log.error(f"Error deleting user: {e}")


    @classmethod
    async def get_bot_stat(cls) -> Dict[str, Any] | str | None:
        async with db.session_factory() as ses:
            now = datetime.utcnow()
            last_day = now - timedelta(days=1)
            last_week = now - timedelta(days=7)
            last_month = now - timedelta(days=30)

            total_users = await UserDAO.count(ses)
            active_users = await UserDAO.count(ses,
                and_(
                    UserModel.energy < cfg.energy_limit,
                    UserModel.referrals_counter >= 1,
                    cast(UserModel.updated_at, Date) == datetime.utcnow().date(),
                )
            )
            blocked_users = await UserDAO.count(ses, is_active=False)

            new_users_last_day = await UserDAO.count(ses, UserModel.created_at >= last_day)
            new_users_last_week = await UserDAO.count(ses, UserModel.created_at >= last_week)
            new_users_last_month = await UserDAO.count(ses, UserModel.created_at >= last_month)

            return {
                "total_users": total_users,
                "active_users": active_users,
                "blocked_users": blocked_users,
                "new_users_last_day": new_users_last_day,
                "new_users_last_week": new_users_last_week,
                "new_users_last_month": new_users_last_month,
            }


    @classmethod
    async def telegram_auth(
            cls,
            tg_id: int,
            auth_timestamp: int
    ):
        async with db.session_factory() as ses:
            db_user = await UserDAO.find_first(ses, tg_id=tg_id)
            if db_user is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User not found"
                )

            current_date = datetime.utcnow().date()
            last_login_date = datetime.fromtimestamp(db_user.auth_date).date() if db_user.auth_date else None

            if last_login_date is None:
                # Первый вход
                db_user.daily_reward_counter = 1
            elif current_date > last_login_date:
                # Пользователь пропустил один или несколько дней
                days_difference = (current_date - last_login_date).days

                if days_difference > 1:
                    # Если пропущено больше одного дня, сбрасываем счётчик
                    db_user.daily_reward_counter = 1
                    # и удаляем записи о выполненных заданиях
                    await UserDailyRewardedTaskDAO.delete(ses, tg_id=db_user.tg_id)
                else:
                    # Если пропущен один день, увеличиваем счётчик
                    db_user.daily_reward_counter += 1
            elif current_date == last_login_date:
                # Пользователь уже заходил сегодня, ничего не делаем
                pass


            daily_reward = await DailyRewardsDAO.find_first(
                ses,
                day_number=db_user.daily_reward_counter
            )
            if daily_reward and daily_reward.day_number == db_user.daily_reward_counter:
                exist_task = await UserDailyRewardedTaskDAO.find_first(
                    ses,
                    tg_id=db_user.tg_id,
                    reward_id=daily_reward.id
                )
                if exist_task is None:
                    await UserDailyRewardedTaskDAO.add(
                        ses,
                        obj_in=UserDailyRewardedTaskCreate(
                            tg_id=db_user.tg_id,
                            reward_id=daily_reward.id,
                            is_claimed=False
                        )
                    )


            if db_user.auth_date != auth_timestamp:
                db_user.auth_date = auth_timestamp

            await ses.commit()
