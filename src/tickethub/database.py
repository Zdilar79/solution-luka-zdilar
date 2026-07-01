from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from tickethub.config import settings

# 1) Engine — tvornica konekcija, jedna za cijelu aplikaciju
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,   # ako je debug=True, ispisuje SQL upite u konzolu
    future=True,
)

# 2) Session factory — iz nje vadimo nove sesije po zahtjevu
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# 3) Base — zajednički "predak" svih naših modela (tablica)
class Base(DeclarativeBase):
    pass


# 4) Dependency — FastAPI će je zvati da dobije sesiju za svaki zahtjev
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
    