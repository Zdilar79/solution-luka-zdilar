from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub import crud
from tickethub.database import get_session
from tickethub.schemas import PaginatedTickets, TicketDetail

router = APIRouter(prefix="/tickets", tags=["tickets"])


# VAŽNO: /search MORA biti prije /{ticket_id} (vidi objašnjenje ispod)
@router.get("/search", response_model=PaginatedTickets)
async def search_tickets(
    q: str = Query(..., min_length=1, description="Pretraga po naslovu"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> PaginatedTickets:
    items, total = await crud.search_tickets(session, q=q, skip=skip, limit=limit)
    return PaginatedTickets(items=items, total=total, skip=skip, limit=limit)


@router.get("", response_model=PaginatedTickets)
async def list_tickets(
    status: str | None = Query(None, description="Filtriraj po statusu"),
    priority: str | None = Query(None, description="Filtriraj po prioritetu"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> PaginatedTickets:
    items, total = await crud.list_tickets(
        session, skip=skip, limit=limit, status=status, priority=priority
    )
    return PaginatedTickets(items=items, total=total, skip=skip, limit=limit)


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: int,
    session: AsyncSession = Depends(get_session),
) -> TicketDetail:
    ticket = await crud.get_ticket(session, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket nije pronađen")
    return ticket