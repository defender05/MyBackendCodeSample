from typing import AsyncGenerator
from typing_extensions import Annotated

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String, MetaData

from src.settings import get_settings
from src.core.constants import DB_NAMING_CONVENTION

cfg = get_settings()

str_256 = Annotated[str, 256]


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)

    type_annotation_map = {
        str_256: String(256)
    }

    repr_cols_num = 10
    repr_cols = tuple()

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"

    # TODO: можно сделать быстрее
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}



class DatabaseHelper:
    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 5,
        pool_pre_ping: bool = True,
        max_overflow: int = 10,
    ) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            pool_pre_ping=pool_pre_ping,
            max_overflow=max_overflow,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.session_factory() as session:
            yield session


db_helper = DatabaseHelper(
    url=str(cfg.async_db_url),
    echo=cfg.db_echo,
    echo_pool=cfg.db_echo_pool,
    pool_size=cfg.db_pool_size,
    pool_pre_ping=cfg.db_pool_pre_ping,
    max_overflow=cfg.db_max_overflow
)