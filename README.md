# TicketHub

Middleware REST servis koji dohvaca "support tickete" iz vanjskog izvora
(DummyJSON), transformira ih u vlastiti model, pohranjuje u PostgreSQL i
izlaze kroz REST API. Svi read i write endpointi rade nad lokalnom bazom,
ne nad zivim pozivom prema DummyJSON-u.

## Tehnologije

- Python 3.11, FastAPI, async/await
- SQLAlchemy 2.0 (async) + asyncpg, PostgreSQL
- Alembic (migracije), httpx (vanjski pozivi), Pydantic v2
- pytest + respx (testovi), GitHub Actions (CI), Docker Compose

## Brzo pokretanje (Docker)

Dize cijeli stack (baza + app), pokrece migracije i server:

    docker compose up -d --build

- API: http://localhost:8000
- Dokumentacija (Swagger): http://localhost:8000/docs

Punjenje baze iz vanjskog izvora:

    docker compose exec app python -m tickethub.sync

## Lokalno pokretanje (bez Dockera za app)

    docker compose up -d db
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -e ".[dev]"
    alembic upgrade head
    python -m tickethub.sync
    uvicorn tickethub.main:app --reload

## Konfiguracija (varijable okruzenja)

Postavke se citaju iz .env (vidi .env.example):

| Varijabla | Opis | Default |
|---|---|---|
| DATABASE_URL | Async URL baze | postgresql+asyncpg://tickethub:tickethub@localhost:5433/tickethub |
| DUMMYJSON_BASE_URL | Bazni URL izvora | https://dummyjson.com |
| SYNC_ON_STARTUP | Sync pri pokretanju | true |
| BACKGROUND_SYNC_INTERVAL_SECONDS | Interval pozadinskog sync-a (0 = iskljuceno) | 0 |

U Dockeru DATABASE_URL koristi host db:5432, lokalno localhost:5433.

## Endpointi

| Metoda | Putanja | Opis |
|---|---|---|
| GET | /tickets | Paginirana lista (filtri: status, priority) |
| GET | /tickets/{id} | Detalj + puni JSON iz izvora |
| GET | /tickets/search?q= | Pretraga po naslovu |
| POST | /tickets | Kreiranje ticketa |
| PATCH | /tickets/{id} | Izmjena ticketa (prezivljava sync i restart) |
| GET | /stats | Agregirane statistike |
| GET | /health | Health-check |

## Model i transformacija

DummyJSON todo se preslikava u Ticket:

- id <- todo.id
- title <- todo.todo
- status <- "closed" ako completed, inace "open"
- priority <- id % 3 -> {0: low, 1: medium, 2: high}
- assignee <- username (preko userId iz /users)
- raw_data <- cijeli originalni todo (za detalj endpoint)

DummyJSON todos nemaju zaseban opis, pa se description izvodi iz teksta
zadatka i skracuje na 100 znakova u listi. Lokalno izmijenjeni ticketi
(is_modified = true) preskacu se pri sync-u, pa korisnicke izmjene
prezivljavaju osvjezavanje iz izvora.

## Testovi

    pytest -v

Zahtijeva pokrenut PostgreSQL (npr. docker compose up -d db).

## Koristenje AI alata

Pri izradi je koristen AI asistent (Claude) za objasnjenja arhitekture,
generiranje boilerplate koda i otklanjanje gresaka (npr. konfiguracija
async SQLAlchemy + Alembic, ON CONFLICT upsert logika, GitHub Actions CI).
Svaka odluka je pregledana i shvacena.
