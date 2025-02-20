from typing import Any

from src.api.schemas.enterprise_schemas import UserEnterpriseCreate
from src.api.services.case_service import CaseService
from src.api.services.user_service import UserService
from src.api.services.enterprise_service import EnterpriseService
from src.api.services.boost_service import BoostService
from src.api.schemas.stars_payment_schemas import StarsPayment, StarsPaymentCreate
from src.api.schemas.boost_schemas import UserBoostCreate
from src.core.models import StarsPaymentModel, StarsRefundModel
from src.api.dao import StarsPaymentDAO
from src.core.database import db_helper as db
from src.api.logging import log


class StarsPaymentService:
    @classmethod
    async def save_payment(
            cls,
            order: StarsPaymentCreate,
    ) -> None:
        async with db.session_factory() as session:
            await StarsPaymentDAO.add(session, order)
            await session.commit()


    @classmethod
    async def buy_product_for_stars(cls, success_order: dict[Any, Any]) -> Any:

        # Покупка слота за старс
        if success_order['product_type'] == 'slot':
            await UserService.buy_slot(int(success_order['user_id']))

        # Покупка предприятия за старс
        elif success_order['product_type'] == 'enterprise':
            ent = UserEnterpriseCreate(
                tg_id=int(success_order['user_id']),
                enterprise_id=int(success_order['product_id']),
            )
            await EnterpriseService.buy_for_stars(ent.tg_id, ent.enterprise_id)

        # Покупка буста за старс
        elif success_order['product_type'] == 'boost':
            user_boost = UserBoostCreate(
                tg_id=int(success_order['user_id']),
                boost_id=int(success_order['product_id']),
            )
            await BoostService.buy_for_stars(user_boost)
            
        # Покупка кейса за старс
        elif success_order['product_type'] == 'case':
            await CaseService.buy_for_stars(
                tg_id=int(success_order['user_id']),
                case_id=int(success_order['product_id']),
            )


    @classmethod
    async def refund_stars(cls, refund: dict[str, Any]) -> Any:
        log.info(f'Refund info: {refund}')
