from datetime import datetime

import httpx

from app.services.data_sources.base import (
    DataRequest,
    DataResult,
    DataSource,
)


class WebDataSource(DataSource):
    def __init__(
        self,
        timeout: float = 15.0,
        max_retries: int = 2,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def name(self) -> str:
        return "web"

    @property
    def source_type(self) -> str:
        return "web"

    async def fetch(self, request: DataRequest) -> DataResult:
        if not request.query.strip():
            return DataResult(
                source=self.name,
                success=False,
                error="Query cannot be empty.",
            )

        params = {
            "q": request.query,
        }

        if request.country:
            params["country"] = request.country

        last_error: str | None = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                ) as client:
                    response = await client.get(
                        "https://www.google.com/search",
                        params=params,
                        headers={
                            "User-Agent": (
                                "Veyra-Finance/1.0 "
                                "(research client)"
                            )
                        },
                    )

                response.raise_for_status()

                return DataResult(
                    source=self.name,
                    success=True,
                    raw=response.text,
                )

            except httpx.HTTPError as exc:
                last_error = str(exc)

                if attempt < self.max_retries:
                    continue

        return DataResult(
            source=self.name,
            success=False,
            error=last_error or "Web request failed.",
        )
