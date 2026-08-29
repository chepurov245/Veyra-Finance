import re
from openai import AsyncOpenAI

from app.core.config import settings
from app.services.data_sources.search import (
    SearchProvider,
    SearchRequest,
    SearchResponse,
    SearchResult,
)



def _extract_published_at(
    text: str,
) -> str | None:
    import re

    months = {
        "января": 1,
        "февраля": 2,
        "марта": 3,
        "апреля": 4,
        "мая": 5,
        "июня": 6,
        "июля": 7,
        "августа": 8,
        "сентября": 9,
        "октября": 10,
        "ноября": 11,
        "декабря": 12,
    }

    russian_pattern = re.compile(
        r"\b(\d{1,2})\s+"
        r"(января|февраля|марта|апреля|мая|июня|"
        r"июля|августа|сентября|октября|ноября|декабря)"
        r"\s+(\d{4})\b",
        re.IGNORECASE,
    )

    numeric_pattern = re.compile(
        r"\b(\d{1,2})[./-]"
        r"(\d{1,2})[./-]"
        r"(\d{4})\b"
    )

    match = russian_pattern.search(text)

    if match:
        day = int(match.group(1))
        month = months.get(
            match.group(2).lower()
        )
        year = int(match.group(3))

        if month:
            return (
                f"{year:04d}-"
                f"{month:02d}-"
                f"{day:02d}"
            )

    match = numeric_pattern.search(text)

    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))

        if (
            1 <= day <= 31
            and 1 <= month <= 12
            and 2000 <= year <= 2100
        ):
            return (
                f"{year:04d}-"
                f"{month:02d}-"
                f"{day:02d}"
            )

    return None

class OpenAIWebSearchProvider(SearchProvider):

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
        return "openai_web"

    async def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:

        query = request.query.strip()

        freshness_terms = (
            "сейчас",
            "текущий",
            "текущая",
            "текущие",
            "актуаль",
            "сегодня",
            "последн",
            "latest",
            "current",
        )

        is_freshness_query = any(
            term in query.lower()
            for term in freshness_terms
        )

        if is_freshness_query:
            query = (
                query
                + "\n\n"
                + "РЕЖИМ: CURRENT / FRESH DATA.\n"
                + "Запрос требует актуальной информации "
                + "на текущую дату.\n"
                + "1. Используй только самые свежие "
                + "доступные фактические данные.\n"
                + "2. Приоритет: официальные источники "
                + "и первичные публикации. Для России "
                + "в первую очередь Росстат, Банк России "
                + "и официальные государственные источники.\n"
                + "3. Не используй данные 2025 года или "
                + "более старые, если доступно значение "
                + "за 2026 год.\n"
                + "4. Не заменяй фактический показатель "
                + "прогнозом или ожиданием.\n"
                + "5. Для каждого числового значения "
                + "определи точную дату или период.\n"
                + "6. Если показатель за текущую дату "
                + "ещё не опубликован, используй последнее "
                + "официально опубликованное значение "
                + "и явно укажи его дату.\n"
                + "7. Не смешивай несколько периодов "
                + "в один текущий показатель.\n"
                + "8. Если источники противоречат друг "
                + "другу, предпочти более свежий первичный "
                + "источник и не скрывай расхождение.\n"
                + "9. Для каждого ключевого числового "
                + "утверждения нужен непосредственный "
                + "источник.\n"
            )

        if not query:
            return SearchResponse(
                provider=self.name,
                success=False,
                error="Search query cannot be empty.",
            )

        try:
            response = await self.client.responses.create(
                model="gpt-4.1-mini",
                tools=[
                    {"type": "web_search_preview"}
                ],
                input=query,
            )

            results: list[SearchResult] = []
            seen_urls: set[str] = set()

            for item in response.output:
                if getattr(
                    item,
                    "type",
                    None,
                ) != "message":
                    continue

                for content_item in getattr(
                    item,
                    "content",
                    [],
                ):
                    if getattr(
                        content_item,
                        "type",
                        None,
                    ) != "output_text":
                        continue

                    text = (
                        getattr(
                            content_item,
                            "text",
                            None,
                        )
                        or ""
                    ).strip()

                    annotations = getattr(
                        content_item,
                        "annotations",
                        [],
                    )

                    for annotation in annotations:
                        if getattr(
                            annotation,
                            "type",
                            None,
                        ) != "url_citation":
                            continue

                        url = getattr(
                            annotation,
                            "url",
                            None,
                        )

                        if (
                            not url
                            or url in seen_urls
                        ):
                            continue

                        seen_urls.add(url)

                        start = getattr(
                            annotation,
                            "start_index",
                            None,
                        )

                        end = getattr(
                            annotation,
                            "end_index",
                            None,
                        )

                        snippet = ""

                        if (
                            isinstance(start, int)
                            and isinstance(end, int)
                            and 0 <= start < end
                            and end <= len(text)
                        ):
                            snippet = (
                                text[start:end]
                                .strip()
                            )

                        if not snippet:
                            snippet = text

                        # The citation range points to
                        # the citation marker itself.
                        # Extract only the claim immediately
                        # preceding this citation.

                        content = ""

                        if (
                            isinstance(start, int)
                            and isinstance(end, int)
                            and 0 <= start < end
                            and end <= len(text)
                        ):
                            before = text[:start]

                            # Find the previous citation marker.
                            previous_citation = before.rfind(
                                "))"
                            )

                            if previous_citation >= 0:
                                claim_start = (
                                    previous_citation + 2
                                )
                            else:
                                claim_start = 0

                            segment = before[
                                claim_start:
                            ].strip()

                            # Remove markdown / paragraph noise.
                            segment = segment.strip()

                            # Take only the final sentence/claim
                            # from the segment.
                            sentence_positions = [
                                segment.rfind(". "),
                                segment.rfind(".\\n"),
                                segment.rfind("! "),
                                segment.rfind("? "),
                            ]

                            boundary = max(
                                sentence_positions
                            )

                            if boundary >= 0:
                                candidate = (
                                    segment[
                                        boundary + 1:
                                    ].strip()
                                )
                            else:
                                candidate = segment

                            # Ignore headings and highlights.
                            if (
                                candidate
                                and not candidate.startswith(
                                    "## "
                                )
                                and not candidate.startswith(
                                    "- ["
                                )
                                and not candidate.startswith(
                                    "["
                                )
                            ):
                                content = candidate

                        if not content:
                            content = (
                                snippet
                                or ""
                            ).strip()

                        published_at = (
                            _extract_published_at(
                                content or snippet or text
                            )
                        )

                        results.append(
                            SearchResult(
                                title=(
                                    getattr(
                                        annotation,
                                        "title",
                                        "",
                                    )
                                    or "Web source"
                                ),
                                url=url,
                                snippet=snippet,
                                source=self.name,
                                published_at=published_at,
                                content=content,
                            )
                        )

            return SearchResponse(
                provider=self.name,
                success=True,
                results=results,
            )

        except Exception as exc:
            return SearchResponse(
                provider=self.name,
                success=False,
                error=str(exc),
            )
