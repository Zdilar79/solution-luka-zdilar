import httpx
import pytest
import respx

from tickethub.external import DummyJSONClient
from tickethub.sync import sync_tickets

# Lažni podaci koje "vraća" DummyJSON u testovima
FAKE_TODOS = {
    "todos": [
        {"id": 1, "todo": "Prvi zadatak", "completed": False, "userId": 1},
        {"id": 2, "todo": "Drugi zadatak", "completed": True, "userId": 2},
    ],
    "total": 2, "skip": 0, "limit": 0,
}
FAKE_USERS = {
    "users": [
        {"id": 1, "username": "ana"},
        {"id": 2, "username": "marko"},
    ],
    "total": 2, "skip": 0, "limit": 0,
}


def _mock_dummyjson(router: respx.MockRouter) -> None:
    router.get("https://dummyjson.com/todos").mock(
        return_value=httpx.Response(200, json=FAKE_TODOS)
    )
    router.get("https://dummyjson.com/users").mock(
        return_value=httpx.Response(200, json=FAKE_USERS)
    )


# ---------- unit test: transformacija ----------

def test_priority_mapping():
    from tickethub.sync import PRIORITY_BY_REMAINDER

    assert PRIORITY_BY_REMAINDER[1 % 3] == "medium"
    assert PRIORITY_BY_REMAINDER[2 % 3] == "high"
    assert PRIORITY_BY_REMAINDER[3 % 3] == "low"


# ---------- integracijski: sync + read ----------

@respx.mock
async def test_sync_populates_db(session):
    _mock_dummyjson(respx.mock)
    count = await sync_tickets(session, client=DummyJSONClient())
    assert count == 2


@respx.mock
async def test_list_and_detail(client, session):
    _mock_dummyjson(respx.mock)
    await sync_tickets(session, client=DummyJSONClient())

    resp = await client.get("/tickets")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

    # status transformacija: id=2 completed=True -> closed
    detail = await client.get("/tickets/2")
    assert detail.status_code == 200
    assert detail.json()["status"] == "closed"
    assert detail.json()["assignee"] == "marko"


async def test_get_missing_returns_404(client):
    resp = await client.get("/tickets/999999")
    assert resp.status_code == 404


# ---------- integracijski: write + štit ----------

async def test_create_ticket(client):
    resp = await client.post("/tickets", json={"title": "Novi", "priority": "high"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Novi"
    assert body["is_modified"] is True


@respx.mock
async def test_patch_survives_sync(client, session):
    _mock_dummyjson(respx.mock)
    await sync_tickets(session, client=DummyJSONClient())

    # izmijeni ticket 1
    patched = await client.patch("/tickets/1", json={"status": "closed"})
    assert patched.status_code == 200
    assert patched.json()["is_modified"] is True

    # ponovni sync NE smije pregaziti izmjenu
    await sync_tickets(session, client=DummyJSONClient())
    after = await client.get("/tickets/1")
    assert after.json()["status"] == "closed"   # ostalo izmijenjeno!


