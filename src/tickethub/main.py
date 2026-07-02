import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from tickethub.config import settings
from tickethub.database import SessionLocal
from tickethub.logging_config import setup_logging
from tickethub.routers import stats, tickets
from tickethub.sync import sync_tickets

logger = logging.getLogger("tickethub")


async def _run_sync_once() -> None:
    try:
        async with SessionLocal() as session:
            count = await sync_tickets(session)
        logger.info("Sync gotov: obrađeno %d ticketa", count)
    except Exception:
        # ne rušimo app ako izvor nije dostupan
        logger.exception("Sync nije uspio")


async def _background_sync(interval: int) -> None:
    while True:
        await asyncio.sleep(interval)
        logger.info("Pokrećem periodički sync...")
        await _run_sync_once()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.debug)
    logger.info("TicketHub se pokreće.")

    if settings.sync_on_startup:
        logger.info("Početni sync iz vanjskog izvora...")
        await _run_sync_once()

    task: asyncio.Task | None = None
    if settings.background_sync_interval_seconds > 0:
        logger.info(
            "Pozadinski sync uključen (svakih %d s).",
            settings.background_sync_interval_seconds,
        )
        task = asyncio.create_task(
            _background_sync(settings.background_sync_interval_seconds)
        )

    yield  # <- ovdje aplikacija radi

    if task is not None:
        task.cancel()
    logger.info("TicketHub se gasi.")


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    line = "%s %s -> %d" % (
        request.method,
        request.url.path,
        response.status_code,
    )
    if response.status_code >= 500:
        logger.error(line)
    elif response.status_code >= 400:
        logger.warning(line)
    else:
        logger.info(line)
    return response


app.include_router(tickets.router)
app.include_router(stats.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}