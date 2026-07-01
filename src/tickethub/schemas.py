from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TicketListItem(BaseModel):
    """Jedan redak u listi — kratak prikaz."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: str
    priority: str
    description: str

    @field_validator("description")
    @classmethod
    def truncate_description(cls, value: str) -> str:
        # zadatak traži opis <= 100 znakova u listi
        return value[:100]


class TicketDetail(BaseModel):
    """Puni detalj ticketa + originalni JSON iz izvora."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    priority: str
    assignee: str | None
    is_modified: bool
    created_at: datetime
    updated_at: datetime
    raw_data: dict


class PaginatedTickets(BaseModel):
    """Omotač oko liste s podacima o paginaciji."""

    items: list[TicketListItem]
    total: int
    skip: int
    limit: int