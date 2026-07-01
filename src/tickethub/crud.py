from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub.models import Ticket


async def list_tickets(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    priority: str | None = None,
) -> tuple[Sequence[Ticket], int]:
    conditions = []
    if status is not None:
        conditions.append(Ticket.status == status)
    if priority is not None:
        conditions.append(Ticket.priority == priority)

    count_stmt = select(func.count()).select_from(Ticket)
    list_stmt = select(Ticket).order_by(Ticket.id).offset(skip).limit(limit)
    if conditions:
        count_stmt = count_stmt.where(*conditions)
        list_stmt = list_stmt.where(*conditions)

    total = await session.scalar(count_stmt) or 0
    result = await session.scalars(list_stmt)
    return result.all(), total


async def get_ticket(session: AsyncSession, ticket_id: int) -> Ticket | None:
    return await session.get(Ticket, ticket_id)


async def search_tickets(
    session: AsyncSession,
    *,
    q: str,
    skip: int = 0,
    limit: int = 20,
) -> tuple[Sequence[Ticket], int]:
    pattern = f"%{q}%"
    condition = Ticket.title.ilike(pattern)

    count_stmt = select(func.count()).select_from(Ticket).where(condition)
    list_stmt = (
        select(Ticket).where(condition).order_by(Ticket.id).offset(skip).limit(limit)
    )

    total = await session.scalar(count_stmt) or 0
    result = await session.scalars(list_stmt)
    return result.all(), total