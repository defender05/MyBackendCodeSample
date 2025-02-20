from src.core.models import (
    UserModel, ReferralModel, StarsPaymentModel,
    CountryModel, RegionModel, EnterpriseModel,
    EnterpriseTypeModel, UserEnterpriseModel,
    BoostModel, UserBoostModel, CaseModel, GdpUserRatingModel, CapacityUserRatingModel,
    RefreshSessionModel, UserRewardedTaskModel, RewardedTaskModel, LevelModel,
    DailyRewardsModel, UserDailyRewardedTaskModel, ReferralRewardsModel,
    UserReferralRewardsModel, UserLevelRewardsModel, MarketEnterpriseModel,
    UserMarketEnterprisePriceModel, UserMarketEnterpriseHistoryModel, CurrencyModel,
)
from src.api.schemas.auth_schemas import RefreshSessionCreate, RefreshSessionUpdate
from src.api.schemas.user_schemas import UserCreate, UserUpdate, UserRewardedTaskCreate, \
    UserDailyRewardedTaskCreate, UserReferralRewardsCreate, UserLevelRewardsCreate
from src.api.schemas.user_referral_schemas import UserReferralCreate, UserReferralUpdate
from src.api.schemas.stars_payment_schemas import StarsPayment, StarsPaymentCreate
from src.api.schemas.country_schemas import CountryCreate, CountryUpdate, RegionCreate, RegionUpdate
from src.api.schemas.enterprise_schemas import EnterpriseCreate, EnterpriseUpdate
from src.api.schemas.enterprise_schemas import EnterpriseTypeCreate, EnterpriseTypeUpdate
from src.api.schemas.enterprise_schemas import UserEnterpriseCreate, UserEnterpriseUpdate
from src.api.schemas.boost_schemas import BoostCreate, BoostUpdate, UserBoostCreate, UserBoostUpdate
from src.api.schemas.market_schemas import (
    MarketCreate,
    UserMarketPriceCreate,
    UserMarketPriceUpdate,
    UserMarketHistoryCreate,
)

from src.core.base_dao import BaseDAO


class RefreshSessionDAO(BaseDAO[RefreshSessionModel, RefreshSessionCreate, RefreshSessionUpdate]):
    model = RefreshSessionModel


class UserDAO(BaseDAO[UserModel, UserCreate, UserUpdate]):
    model = UserModel


class CurrencyDAO(BaseDAO[CurrencyModel, None, None]):
    model = CurrencyModel


class LevelDAO(BaseDAO[LevelModel, None, None]):
    model = LevelModel


class UserReferralDAO(BaseDAO[ReferralModel, UserReferralCreate, UserReferralUpdate]):
    model = ReferralModel


class GdpUserRatingDAO(BaseDAO[GdpUserRatingModel, None, None]):
    model = GdpUserRatingModel


class CapacityUserRatingDAO(BaseDAO[CapacityUserRatingModel, None, None]):
    model = CapacityUserRatingModel


class EnterpriseDAO(BaseDAO[EnterpriseModel, EnterpriseCreate, EnterpriseUpdate]):
    model = EnterpriseModel


class EnterpriseTypeDAO(BaseDAO[EnterpriseTypeModel, EnterpriseTypeCreate, EnterpriseTypeUpdate]):
    model = EnterpriseTypeModel


class UserEnterpriseDAO(BaseDAO[UserEnterpriseModel, UserEnterpriseCreate, UserEnterpriseUpdate]):
    model = UserEnterpriseModel



class StarsPaymentDAO(BaseDAO[StarsPaymentModel, StarsPaymentCreate, None]):
    model = StarsPaymentModel


class CountryDAO(BaseDAO[CountryModel, CountryCreate, CountryUpdate]):
    model = CountryModel


class RegionDAO(BaseDAO[RegionModel, RegionCreate, RegionUpdate]):
    model = RegionModel


class BoostDAO(BaseDAO[BoostModel, BoostCreate, BoostUpdate]):
    model = BoostModel


class UserBoostDAO(BaseDAO[UserBoostModel, UserBoostCreate, UserBoostUpdate]):
    model = UserBoostModel


class CaseDAO(BaseDAO[CaseModel, None, None]):
    model = CaseModel


class RewardedTaskDAO(BaseDAO[RewardedTaskModel, None, None]):
    model = RewardedTaskModel


class UserRewardedTaskDAO(BaseDAO[UserRewardedTaskModel, UserRewardedTaskCreate, None]):
    model = UserRewardedTaskModel


class DailyRewardsDAO(BaseDAO[DailyRewardsModel, None, None]):
    model = DailyRewardsModel


class UserDailyRewardedTaskDAO(BaseDAO[UserDailyRewardedTaskModel, UserDailyRewardedTaskCreate, None]):
    model = UserDailyRewardedTaskModel


class ReferralRewardsDAO(BaseDAO[ReferralRewardsModel, None, None]):
    model = ReferralRewardsModel


class UserReferralRewardsDAO(BaseDAO[UserReferralRewardsModel, UserReferralRewardsCreate, None]):
    model = UserReferralRewardsModel


class UserLevelRewardsDAO(BaseDAO[UserLevelRewardsModel, UserLevelRewardsCreate, None]):
    model = UserLevelRewardsModel


class MarketDAO(BaseDAO[MarketModel, MarketCreate, None]):
    model = MarketModel


class UserMarketPricesDAO(BaseDAO[UserMarketPriceModel, UserMarketPriceCreate, UserMarketPriceUpdate]):
    model = UserMarketPriceModel


class UserMarketHistoryDAO(BaseDAO[UserMarketHistoryModel, UserMarketHistoryCreate, None]):
    model = UserMarketHistoryModel
