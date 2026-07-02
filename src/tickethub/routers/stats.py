from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub import crud
from tickethub.database import get_session
from tickethub.schemas import TicketStats

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=TicketStats)
async def get_stats(
    session: AsyncSession = Depends(get_session),
) -> TicketStats:
    data = await crud.get_stats(session)
    return TicketStats(**data)