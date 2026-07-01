from fastapi import FastAPI

from tickethub.config import settings
from tickethub.routers import tickets

app = FastAPI(title=settings.app_name)

app.include_router(tickets.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}