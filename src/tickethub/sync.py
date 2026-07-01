import asyncio

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from tickethub.database import SessionLocal, engine
from tickethub.external import DummyJSONClient
from tickethub.models import Ticket

# id % 3 -> prioritet (dokumentirana odluka)
PRIORITY_BY_REMAINDER = {0: "low", 1: "medium", 2: "high"}


def _transform(todo: dict, usernames_by_id: dict[int, str]) -> dict:
    return {
        "id": todo["id"],
        "title": todo["todo"],
        # todos nemaju zaseban opis -> koristimo tekst zadatka kao opis
        "description": todo["todo"],
        "status": "closed" if todo["completed"] else "open",
        "priority": PRIORITY_BY_REMAINDER[todo["id"] % 3],
        "assignee": usernames_by_id.get(todo["userId"]),
        "raw_data": todo,
    }


async def sync_tickets(
    session: AsyncSession, client: DummyJSONClient | None = None
) -> int:
    client = client or DummyJSONClient()
    todos, users = await client.fetch_source_data()

    usernames_by_id = {u["id"]: u["username"] for u in users}
    rows = [_transform(todo, usernames_by_id) for todo in todos]
    if not rows:
        return 0

    stmt = pg_insert(Ticket).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "title": stmt.excluded.title,
            "description": stmt.excluded.description,
            "status": stmt.excluded.status,
            "priority": stmt.excluded.priority,
            "assignee": stmt.excluded.assignee,
            "raw_data": stmt.excluded.raw_data,
            "updated_at": func.now(),
        },
        where=Ticket.is_modified.is_(False),
    )
    await session.execute(stmt)
    await session.commit()
    return len(rows)


async def _run() -> None:
    async with SessionLocal() as session:
        count = await sync_tickets(session)
        print(f"Sync gotov: obrađeno {count} ticketa.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_run())