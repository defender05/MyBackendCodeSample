from datetime import *
from decimal import *
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# TODO: Большая часть моделей удалена. Оставлены только базовые для примера
# relatioship'ы пока автоматически не генерятся

class RefreshSessionModel(Base):
    __tablename__ = 'refresh_session'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    refresh_token: Mapped[UUID] = mapped_column(nullable=False)
    expires_in: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(column='users.id', onupdate='NO ACTION', ondelete='CASCADE'),
        nullable=False
    )



class CurrenciesModel(Base):
    __tablename__ = 'currencies'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    code: Mapped[str] = mapped_column(nullable=True)
    name: Mapped[str] = mapped_column(nullable=True)



class MarketModel(Base):
    __tablename__ = 'market'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    tg_id: Mapped[int] = mapped_column(
        ForeignKey(column='users.tg_id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    enterprise_id: Mapped[int] = mapped_column(
        ForeignKey(column='enterprises.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(nullable=True)
    
    user = relationship(
        'UserModel',
        back_populates='enterprises_ads',
        foreign_keys=[tg_id]
    )
    enterprise = relationship(
        'EnterpriseModel',
        back_populates='market_ads',
        foreign_keys=[enterprise_id]
    )
    prices = relationship(
        'UserMarketPriceModel',
        back_populates='market_ad',
        uselist=True
    )



class UserMarketPricesModel(Base):
    __tablename__ = 'user_market_prices'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    market_id: Mapped[int] = mapped_column(
        ForeignKey(column='market.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    currency_id: Mapped[int] = mapped_column(
        ForeignKey(column='currencies.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=True
    )

    price: Mapped[int] = mapped_column(nullable=True)
    
    market_ad = relationship(
        'MarketModel',
        back_populates='prices',
        uselist=True
    )



class UserMarketHistoryModel(Base):
    __tablename__ = 'user_market_history'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False)
    tg_id: Mapped[int] = mapped_column(
        ForeignKey(column='users.tg_id', onupdate='CASCADE', ondelete='NO ACTION'),
        nullable=True
    )

    enterprise_id: Mapped[int] = mapped_column(
        ForeignKey(column='enterprises.id', onupdate='CASCADE', ondelete='NO ACTION'),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(nullable=True)
    buyer_id: Mapped[UUID] = mapped_column(
        ForeignKey(column='users.id', onupdate='CASCADE', ondelete='NO ACTION'),
        nullable=True
    )

    sold_at: Mapped[datetime] = mapped_column(nullable=True)
    
    enterprise = relationship(
        'EnterpriseModel',
        back_populates='market_history',
        foreign_keys=[enterprise_id]
    )




class UsersModel(Base):
    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(primary_key=True, nullable=False)
    username: Mapped[str] = mapped_column(nullable=True)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    tg_id: Mapped[int] = mapped_column(nullable=False)
    tg_url: Mapped[str] = mapped_column(nullable=True)
    tg_chat_id: Mapped[int] = mapped_column(nullable=True)
    is_bot: Mapped[bool] = mapped_column(nullable=True)
    country_id: Mapped[int] = mapped_column(
        ForeignKey(column='countries.id', onupdate='CASCADE', ondelete='SET DEFAULT'),
        nullable=True
    )

    region_id: Mapped[int] = mapped_column(
        ForeignKey(column='regions.id', onupdate='CASCADE', ondelete='SET DEFAULT'),
        nullable=True
    )

    total_capacity: Mapped[int] = mapped_column(nullable=True)
    users_rating_position: Mapped[int] = mapped_column(nullable=True)
    energy: Mapped[int] = mapped_column(nullable=True)
    enterprises_slots: Mapped[int] = mapped_column(nullable=True)
    game_balance: Mapped[int] = mapped_column(nullable=True)
    referrer_id: Mapped[UUID] = mapped_column(
        ForeignKey(column='users.id', onupdate='CASCADE', ondelete='SET NULL'),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    is_superuser: Mapped[bool] = mapped_column(nullable=True)
    is_verified: Mapped[bool] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=True)
    total_boost_value: Mapped[float] = mapped_column(nullable=True)
    capacity_rating_position: Mapped[int] = mapped_column(nullable=True)
    can_open_case: Mapped[bool] = mapped_column(nullable=True)
    level: Mapped[int] = mapped_column(nullable=True)
    daily_reward_counter: Mapped[int] = mapped_column(nullable=True)
    is_premium: Mapped[bool] = mapped_column(nullable=True)
    referrals_counter: Mapped[int] = mapped_column(nullable=True)
    auth_date: Mapped[int] = mapped_column(nullable=True)
    
    # RELATIONSHIPS --------------------------
    country: Mapped["CountryModel"] = relationship(
        back_populates="users",
        uselist=False,
    )
    # server_default='1'
    region: Mapped["RegionModel"] = relationship(
        back_populates="users",
        uselist=False,
    )
    stars_payments: Mapped["StarsPaymentModel"] = relationship(
        back_populates="user",
        uselist=True,
    )
    stars_refunds: Mapped["StarsRefundModel"] = relationship(
        back_populates="user",
        uselist=True,
    )
    boosts: Mapped[List["UserBoostModel"]] = relationship(
        back_populates="user",
        uselist=True
    )
    enterprises: Mapped[List["UserEnterpriseModel"]] = relationship(
        back_populates="user",
        uselist=True,
    )
    enterprises_ads = relationship(
        'MarketModel',
        back_populates='user',
        uselist=True
    )
    referrals = relationship(
        'ReferralModel',
        back_populates='owner',
        foreign_keys="ReferralModel.owner_id"
    )
    rewards: Mapped[List["UserRewardedTaskModel"]] = relationship(
        back_populates="user",
    )
    daily_rewards: Mapped[List["UserDailyRewardedTaskModel"]] = relationship(
        back_populates="user",
    )
    referral_rewards: Mapped[List["UserReferralRewardsModel"]] = relationship(
        back_populates="user",
    )
    level_rewards: Mapped[List["UserLevelRewardsModel"]] = relationship(
        back_populates="user",
    )



class StarsPaymentsModel(Base):
    __tablename__ = 'stars_payments'

    id: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False)
    total_amount: Mapped[int] = mapped_column(nullable=False)
    provider_payment_charge_id: Mapped[str] = mapped_column(nullable=True)
    shipping_option_id: Mapped[str] = mapped_column(nullable=True)
    invoice_payload: Mapped[dict] = mapped_column(nullable=True)
    order_info: Mapped[dict] = mapped_column(nullable=True)
    tg_id: Mapped[int] = mapped_column(
        ForeignKey(column='users.tg_id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(nullable=False)



class StarsRefundsModel(Base):
    __tablename__ = 'stars_refunds'

    id: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False)
    total_amount: Mapped[int] = mapped_column(nullable=False)
    shipping_option_id: Mapped[str] = mapped_column(nullable=True)
    order_info: Mapped[dict] = mapped_column(nullable=True)
    tg_id: Mapped[int] = mapped_column(
        ForeignKey(column='users.tg_id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(nullable=False)