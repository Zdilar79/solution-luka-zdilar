import httpx

from tickethub.config import settings


class DummyJSONClient:
    """Klijent za dohvat izvornih podataka s DummyJSON-a."""

    def __init__(
        self, base_url: str | None = None, timeout: float | None = None
    ) -> None:
        self.base_url = (base_url or settings.dummyjson_base_url).rstrip("/")
        self.timeout = timeout or settings.http_timeout

    async def fetch_source_data(self) -> tuple[list[dict], list[dict]]:
        """Vrati (todos, users) — SVE zapise, ne samo prvih 30."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            todos_resp = await client.get(
                f"{self.base_url}/todos", params={"limit": 0}
            )
            todos_resp.raise_for_status()

            users_resp = await client.get(
                f"{self.base_url}/users",
                params={"limit": 0, "select": "id,username"},
            )
            users_resp.raise_for_status()

        return todos_resp.json()["todos"], users_resp.json()["users"]