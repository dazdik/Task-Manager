import contextlib
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.db.settings_db import settings

db_url: str = (
    f"postgresql+asyncpg://{settings.DB.USER}:"
    f"{settings.DB.PASSWORD}@{settings.DB.HOSTNAME}:"
    f"{settings.DB.PORT}/{settings.DB.NAME}"
)


class DBSessionManager:
    def __init__(self, url: str, echo: bool = False):
        self.engine = create_async_engine(url=url, echo=echo)
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def close(self):
        if self.engine is None:
            raise Exception("DatabaseSessionManager не инициализирован")
        await self.engine.dispose()

        self.engine = None
        self.session_maker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self.engine is None:
            raise Exception("DBSessionManager не инициализирован")

        async with self.engine.begin() as conn:
            try:
                yield conn
            except Exception:
                await conn.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self.session_maker is None:
            raise Exception("DBSessionManager не инициализирован")

        session = self.session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DBSessionManager(url=db_url, echo=False)


async def get_db_session():
    async with sessionmanager.session() as session:
        yield session
