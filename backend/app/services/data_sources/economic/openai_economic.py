import json

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.data_sources.economic.provider import (
    EconomicDataProvider,
    EconomicDataPoint,
    EconomicDataRequest,
    EconomicDataResponse,
)


class OpenAIEconomicDataProvider(EconomicDataProvider):

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

    @property
    def name(self) -> str:
        return "openai_economic"

    async def get_data(
        self,
        request: EconomicDataRequest,
    ) -> EconomicDataResponse:

        query = f"""
Исследуй экономический показатель:

Показатель: {request.indicator}
Страна: {request.country or "не указана"}
Период от: {request.start_date or "не указан"}
Период до: {request.end_date or "не указан"}

Используй web search.

Приоритет источников:

1. Официальные статистические органы.
2. Центральные банки.
3. Государственные органы.
4. Eurostat.
5. Другие первичные источники.
6. Вторичные источники только если первичные недоступны.

Требования:

- Используй только фактические данные.
- Не используй прогноз вместо фактического значения.
- Найди наиболее свежее доступное фактическое значение.
- Период показателя и дату публикации не смешивай.
- Если найдено несколько значений одного показателя,
  выбери наиболее свежее релевантное значение.
- Не смешивай разные периоды.
- Укажи единицу измерения.
- Укажи источник.
- Укажи URL первоисточника.
- Не придумывай значения.
"""

        try:
            response = await self.client.responses.create(
                model="gpt-4.1-mini",
                tools=[
                    {
                        "type": "web_search_preview"
                    }
                ],
                input=query,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "economic_data",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "data": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "indicator": {
                                                "type": "string"
                                            },
                                            "value": {
                                                "type": "number"
                                            },
                                            "unit": {
                                                "type": [
                                                    "string",
                                                    "null"
                                                ]
                                            },
                                            "country": {
                                                "type": [
                                                    "string",
                                                    "null"
                                                ]
                                            },
                                            "period": {
                                                "type": [
                                                    "string",
                                                    "null"
                                                ]
                                            },
                                            "source": {
                                                "type": "string"
                                            },
                                            "url": {
                                                "type": [
                                                    "string",
                                                    "null"
                                                ]
                                            }
                                        },
                                        "required": [
                                            "indicator",
                                            "value",
                                            "unit",
                                            "country",
                                            "period",
                                            "source",
                                            "url"
                                        ],
                                        "additionalProperties": False
                                    }
                                }
                            },
                            "required": [
                                "data"
                            ],
                            "additionalProperties": False
                        }
                    }
                }
            )

            raw_text = (
                response.output_text or ""
            ).strip()

            if not raw_text:
                return EconomicDataResponse(
                    provider=self.name,
                    success=False,
                    error="No economic data returned.",
                )

            try:
                parsed = json.loads(
                    raw_text
                )

            except json.JSONDecodeError as exc:
                return EconomicDataResponse(
                    provider=self.name,
                    success=False,
                    error=(
                        "Economic provider returned "
                        f"invalid JSON: {exc}"
                    ),
                )

            data: list[EconomicDataPoint] = []

            for item in parsed.get(
                "data",
                [],
            ):

                if not isinstance(item, dict):
                    continue

                value = item.get("value")

                if value is None:
                    continue

                data.append(
                    EconomicDataPoint(
                        indicator=str(
                            item.get(
                                "indicator",
                                "other",
                            )
                        ).strip(),

                        value=float(value),

                        unit=(
                            str(item["unit"])
                            if item.get("unit")
                            is not None
                            else None
                        ),

                        country=(
                            str(item["country"])
                            if item.get("country")
                            is not None
                            else None
                        ),

                        period=(
                            str(item["period"])
                            if item.get("period")
                            is not None
                            else None
                        ),

                        source=str(
                            item.get(
                                "source",
                                "",
                            )
                        ).strip(),

                        url=(
                            str(item["url"])
                            if item.get("url")
                            is not None
                            else None
                        ),
                    )
                )

            data = self._select_latest(
                data
            )

            return EconomicDataResponse(
                provider=self.name,
                success=True,
                data=data,
            )

        except Exception as exc:
            return EconomicDataResponse(
                provider=self.name,
                success=False,
                error=str(exc),
            )

    @staticmethod
    def _select_latest(
        data: list[EconomicDataPoint],
    ) -> list[EconomicDataPoint]:

        groups: dict[
            tuple[str, str | None],
            list[EconomicDataPoint],
        ] = {}

        for item in data:

            key = (
                item.indicator,
                item.country,
            )

            groups.setdefault(
                key,
                [],
            ).append(item)

        selected = []

        for items in groups.values():

            items.sort(
                key=OpenAIEconomicDataProvider._period_key,
                reverse=True,
            )

            selected.append(
                items[0]
            )

        return selected

    @staticmethod
    def _period_key(
        item: EconomicDataPoint,
    ) -> tuple[int, int]:

        period = (
            item.period or ""
        )

        import re

        match = re.search(
            r"(20\d{2})[-/](\d{1,2})",
            period,
        )

        if match:
            return (
                int(match.group(1)),
                int(match.group(2)),
            )

        match = re.search(
            r"(20\d{2})",
            period,
        )

        if match:
            return (
                int(match.group(1)),
                0,
            )

        return (
            0,
            0,
        )
