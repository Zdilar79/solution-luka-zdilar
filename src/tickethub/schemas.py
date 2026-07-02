from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Dozvoljene vrijednosti — Pydantic sam odbije sve izvan ovoga
Status = Literal["open", "closed"]
Priority = Literal["low", "medium", "high"]


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


class TicketCreate(BaseModel):
    """Ulaz za POST /tickets."""

    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    status: Status = "open"
    priority: Priority = "medium"
    assignee: str | None = None


class TicketUpdate(BaseModel):
    """Ulaz za PATCH /tickets/{id} — sva polja opcionalna."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    assignee: str | None = None