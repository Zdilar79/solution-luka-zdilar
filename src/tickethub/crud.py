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


async def create_ticket(session: AsyncSession, data: dict) -> Ticket:
    # id dodjeljujemo sami (autoincrement je isključen jer normalno dolazi iz izvora)
    max_id = await session.scalar(select(func.max(Ticket.id)))
    new_id = (max_id or 0) + 1

    ticket = Ticket(id=new_id, is_modified=True, raw_data={}, **data)
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def update_ticket(
    session: AsyncSession, ticket_id: int, changes: dict
) -> Ticket | None:
    ticket = await session.get(Ticket, ticket_id)
    if ticket is None:
        return None

    for field, value in changes.items():
        setattr(ticket, field, value)

    ticket.is_modified = True  # <- štit: sljedeći sync neće pregaziti ovaj ticket
    await session.commit()
    await session.refresh(ticket)
    return ticket


async def get_stats(session: AsyncSession) -> dict:
    total = await session.scalar(select(func.count()).select_from(Ticket)) or 0

    status_rows = await session.execute(
        select(Ticket.status, func.count()).group_by(Ticket.status)
    )
    priority_rows = await session.execute(
        select(Ticket.priority, func.count()).group_by(Ticket.priority)
    )
    modified = await session.scalar(
        select(func.count())
        .select_from(Ticket)
        .where(Ticket.is_modified.is_(True))
    ) or 0

    return {
        "total": total,
        "by_status": {status: count for status, count in status_rows.all()},
        "by_priority": {priority: count for priority, count in priority_rows.all()},
        "modified": modified,
    }