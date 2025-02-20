from typing import Any, Union, Dict, Callable, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from src.core.database import db_helper as db
from core.utils import get_translation
from src.core.dependencies import get_current_user

from api.dao import UserEnterpriseDAO, MarketDAO, UserMarketPricesDAO, CurrencyDAO, UserDAO, \
    UserMarketHistoryDAO, MarketModel, UserMarketPriceModel, \
    UserMarketHistoryModel, EnterpriseDAO

from src.core.schemas import Pagination
from api.schemas.market_schemas import UserMarketHistoryCreate, Market, \
    UserMarketPriceCreate, MarketCreate
from api.schemas.enterprise_schemas import (
    Enterprise,
    UserEnterpriseCreate
)

from src.settings import get_settings
from loguru import logger as log

cfg = get_settings()

market_router = APIRouter(tags=["Market"], prefix="/market")


@market_router.get("/ads")
async def get_market_ads_by_filter(
        request: Request,
        capacity: Optional[int] = None,
        currency_id: Optional[int] = None,
        type_id: Optional[int] = None,
        price_down: Optional[int] = None,
        price_up: Optional[int] = None,
        pag: Pagination = Depends(Pagination),
        user: Dict[str, Any] = Depends(get_current_user),
) -> list[Dict[str, Any]]:
    """
    Получение списка объявлений на маркете по фильтрам
    """
    async with db.session_factory() as ses:
        stmt = (
            select(MarketModel)
            .options(joinedload(MarketModel.enterprise))
            .options(selectinload(MarketModel.prices))
            .limit(pag.limit)
            .offset(pag.offset)
        )
        if capacity:
            stmt = stmt.filter(MarketModel.enterprise.has(capacity=capacity))
        if currency_id:
            stmt = stmt.filter(MarketModel.prices.any(currency_id=currency_id))
        if type_id:
            stmt = stmt.filter(MarketModel.enterprise.has(type_id=type_id))
        if price_down:
            stmt = stmt.filter(MarketModel.prices.any(price_down <= UserMarketPriceModel.price))
        if price_up:
            stmt = stmt.filter(MarketModel.prices.any(UserMarketPriceModel.price <= price_up))

        result = await ses.execute(stmt)
        market_ads = result.scalars().all()

    _ = get_translation(request=request, domain='enterprises')

    return [
        {
            **item.to_dict(),
            "enterprise": Enterprise(
                id=item.enterprise.id,
                name=_(item.enterprise.name),
                description=_(item.enterprise.description),
                image_url=item.enterprise.image_url,
                type_id=item.enterprise.type_id,
                capacity=item.enterprise.capacity,
                game_price=item.enterprise.game_price,
                stars_price=item.enterprise.stars_price,
            ).dict(),
            "prices": [price.to_dict() for price in item.prices]
        }
        for item in market_ads
    ] if market_ads else []


@market_router.get("/userActiveAds")
async def get_user_active_ads(
        request: Request,
        pag: Pagination = Depends(Pagination),
        user: Dict[str, Any] = Depends(get_current_user),
) -> list[Dict[str, Any]]:
    """
    Получение списка активных объявлений на маркете для текущего юзера
    """
    async with db.session_factory() as ses:
        # Создаем запрос с использованием join и подгрузкой связанных данных
        stmt = (
            select(MarketModel)
            .options(joinedload(MarketModel.enterprise))
            .options(selectinload(MarketModel.prices))
            .where(MarketModel.tg_id == user.get("tg_id"))
            .limit(pag.limit)
            .offset(pag.offset)
        )

        result = await ses.execute(stmt)
        market_enterprises = result.scalars().all()

    _ = get_translation(request=request, domain='enterprises')

    return [
        {
            **item.to_dict(),
            "enterprise": Enterprise(
                id=item.enterprise.id,
                name=_(item.enterprise.name),
                description=_(item.enterprise.description),
                image_url=item.enterprise.image_url, # объект Enterprise тут нужен из-за валидатора в этом поле
                type_id=item.enterprise.type_id,
                capacity=item.enterprise.capacity,
                game_price=item.enterprise.game_price,
                stars_price=item.enterprise.stars_price,
            ).dict(),
            "prices": [price.to_dict() for price in item.prices]
        }
        for item in market_enterprises
    ] if market_enterprises else []



@market_router.get("/userAdsHistory")
async def get_market_history(
        request: Request,
        pag: Pagination = Depends(Pagination),
        user: Dict[str, Any] = Depends(get_current_user),
) -> list[Dict[str, Any]]:
    """
    Получение истории завершенных объявлений на маркете для текущего юзера
    """
    async with db.session_factory() as ses:
        stmt = (
            select(UserMarketHistoryModel)
            .options(joinedload(UserMarketHistoryModel.enterprise))
            .where(UserMarketHistoryModel.tg_id == user.get("tg_id"))
            .limit(pag.limit)
            .offset(pag.offset)
        )

        result = await ses.execute(stmt)
        market_history = result.scalars().all()

    _ = get_translation(request=request, domain='enterprises')
    return [
        {
            **item.to_dict(),
            "enterprise": Enterprise(
                id=item.enterprise.id,
                name=_(item.enterprise.name) if _ else item.enterprise.name,
                description=_(item.enterprise.description) if _ else item.enterprise.description,
                image_url=item.enterprise.image_url,
                type_id=item.enterprise.type_id,
                capacity=item.enterprise.capacity,
                game_price=item.enterprise.game_price,
                stars_price=item.enterprise.stars_price,
            ).dict(),
        }
        for item in market_history
    ] if market_history else []


@market_router.post("/create")
async def create_enterprise_ad(
        enterprise_id: int,
        currency_id: int,
        price: int,
        user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Создание нового объявления на маркете
    """
    async with db.session_factory() as ses:
        user_ents = await UserEnterpriseDAO.find_first(ses, tg_id=user.get("tg_id"), enterprise_id=enterprise_id)
        if not user_ents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The user does not have any purchased enterprises for sale in market"
            )

        new_ad = await MarketDAO.add(ses, obj_in=MarketCreate(
            tg_id=user.get("tg_id"), enterprise_id=enterprise_id)
        )
  
        await ses.flush()  # Выполняем flush, чтобы получить id новой записи

        start_price = await UserMarketPricesDAO.add(ses, obj_in=UserMarketPriceCreate(
            market_enterprise_id=new_ad.id, currency_id=currency_id, price=price
        ))

        # удаляем выставленное на продажу предприятие из таблицы user_enterprises
        await ses.delete(user_ents)
        await ses.commit()

    return {'created_ad': new_ad.to_dict(), 'price': start_price.to_dict()}



@market_router.post("/addPrice")
async def add_price_in_ad(
        price: UserMarketPriceCreate = Depends(UserMarketPriceCreate),
        user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Создание новой цены для указанного объявления \n
    1 валюта = 1 цена \n
    market_enterprise_id - это id объявления из таблицы market_enterprises
    """
    async with db.session_factory() as ses:
        exist_prices = await UserMarketPricesDAO.find_all(
            ses, market_enterprise_id=price.market_enterprise_id
        )
        currencies_set = set(map(lambda x: x.currency_id, exist_prices))
        if price.currency_id in currencies_set:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Price for this currency already exists"
            )

        new_price = await UserMarketPricesDAO.add(
            ses, obj_in=UserMarketPriceCreate(
                market_enterprise_id=price.market_enterprise_id,
                currency_id=price.currency_id,
                price=price.price
            )
        )
        await ses.commit()

    return new_price.to_dict()


@market_router.post("/buy")
async def buy_enterprise_on_market(
        request: Request,
        market_id: int,
        currency_id: int,
        user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Покупка предприятия на маркете \n
    """
    async with db.session_factory() as ses:
        currency = await CurrencyDAO.find_one_or_none(ses, id=currency_id)
        if not currency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Currency not found"
            )

        target_ad = await MarketDAO.find_one_or_none(
            ses, id=market_id
        )
        if not target_ad:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The ad does not exist"
            )

        prices = await UserMarketPricesDAO.find_all(
            ses, market_id=market_id
        )

        target_price = [item for item in prices if item.currency_id == currency_id]
        if target_price is None or len(target_price) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Price for this currency not found"
            )
        target_price = target_price[0]

        buyer_user = await UserDAO.find_one_or_none(ses, tg_id=user.get('tg_id'))
        seller_user = await UserDAO.find_one_or_none(ses, tg_id=target_ad.tg_id)
        if not buyer_user or not seller_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Buyer user or Seller user not found"
            )

        buyed_ad = None
        buyed_enterprise = None

        if currency.code == 'GDP':
            if buyer_user.game_balance < target_price.price:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough gdp"
                )
            else:
                buyer_user.game_balance = buyer_user.game_balance - target_price.price
                seller_user.game_balance = seller_user.game_balance + target_price.price
                # Добавляем купленное предприятие покупателю
                buyed_ad = await UserEnterpriseDAO.add(
                    ses, obj_in=UserEnterpriseCreate(
                        tg_id=buyer_user.tg_id,
                        enterprise_id=target_ad.enterprise_id,
                    )
                )
                buyed_enterprise = await EnterpriseDAO.find_one_or_none(
                    ses, id=buyed_ad.enterprise_id
                )

                # Удаляем объявление с маркета
                await MarketDAO.delete(
                    ses, id=market_id
                )
                # Создаем запись в истории продаж
                await UserMarketHistoryDAO.add(
                    ses, obj_in=UserMarketHistoryCreate(
                        tg_id=seller_user.tg_id,
                        enterprise_id=target_ad.enterprise_id,
                        buyer_id=buyer_user.id,
                        sold_currency_id=currency.id,
                        sold_price=target_price.price,
                    )
                )
                await ses.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Other currencies are currently not supported."
            )

    _ = get_translation(request=request, domain='enterprises')

    return {
        **buyed_ad.to_dict(),
        'enteprise': Enterprise(
            id=buyed_enterprise.id,
            name=_(buyed_enterprise.name) if _ else buyed_enterprise.name,
            description=_(buyed_enterprise.description) if _ else buyed_enterprise.description,
            image_url=buyed_enterprise.image_url,
            type_id=buyed_enterprise.type_id,
            capacity=buyed_enterprise.capacity,
            game_price=buyed_enterprise.game_price,
            stars_price=buyed_enterprise.stars_price,
        ).dict()
    } if buyed_ad else {}
