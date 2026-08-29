from datetime import datetime

from app.services.data_sources.search import SearchResponse
from app.services.intelligence.evidence import Evidence
from app.services.intelligence.source_reliability import (
    classify_source,
)
from app.services.intelligence.source_ranking import (
    SourceRanker,
)


class EvidenceExtractor:

    def __init__(self) -> None:
        self.source_ranker = SourceRanker()


    @staticmethod
    def _extract_period(
        claim: str,
    ) -> str | None:
        import re

        patterns = [
            r"\bс\s+\d{1,2}\s+"
            r"(?:по|-)\s+\d{1,2}\s+"
            r"(?:января|февраля|марта|апреля|мая|июня|"
            r"июля|августа|сентября|октября|ноября|декабря)"
            r"\s+\d{4}\b",

            r"\b(?:в\s+)?"
            r"(?:январе|феврале|марте|апреле|мае|июне|"
            r"июле|августе|сентябре|октябре|ноябре|декабре)"
            r"\s+\d{4}\b",

            r"\b\d{1,2}\s*[–-]\s*\d{1,2}\s+"
            r"(?:января|февраля|марта|апреля|мая|июня|"
            r"июля|августа|сентября|октября|ноября|декабря)"
            r"\s+\d{4}\b",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                claim,
                re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None


    def extract(
        self,
        response: SearchResponse,
        domain=None,
    ) -> list[Evidence]:

        if not response.success:
            return []

        evidence: list[Evidence] = []


        for result in response.results:
            # Prefer source-specific content.
            # `snippet` may contain only a citation marker
            # for OpenAI Web Search.
            claim = (
                result.content
                or result.snippet
                or ""
            ).strip()

            # Без claim источник не может быть
            # доказательством конкретного утверждения.
            if not claim:
                continue

            reliability = classify_source(
                result.url
            )

            base_confidence = (
                self._initial_confidence(
                    reliability
                )
            )

            source_score = self.source_ranker.rank(
                url=result.url,
                domain=domain,
            )

            confidence = min(
                base_confidence,
                source_score.score,
            )

            published_at = (
                self._parse_published_at(
                    result.published_at
                )
            )

            period = self._extract_period(
                claim
            )

            evidence.append(
                Evidence(
                    claim=claim,
                    source_name=(
                        result.source
                        or response.provider
                    ),
                    source_type="web",
                    url=result.url or None,
                    published_at=published_at,
                    confidence=confidence,
                    source_reliability=reliability,
                    metadata={
                        "title": result.title,
                        "published_at": (
                            result.published_at
                        ),
                        "period": period,
                    },
                )
            )

        return evidence

    @staticmethod
    def _parse_published_at(
        value: str | None,
    ) -> datetime | None:

        if not value:
            return None

        value = value.strip()

        if not value:
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None

    @staticmethod
    def _initial_confidence(
        reliability,
    ) -> float:

        if reliability.value >= 4:
            return 0.90

        if reliability.value >= 3:
            return 0.80

        if reliability.value >= 2:
            return 0.60

        return 0.30
