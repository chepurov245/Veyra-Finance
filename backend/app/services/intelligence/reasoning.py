from dataclasses import dataclass, field

from app.services.intelligence.analysis_engine import (
    AnalysisResult,
)
from app.services.intelligence.task_types import (
    AnalysisTask,
)


@dataclass
class ReasoningResult:
    answer: str
    confidence: float
    verified: bool

    citations: list[str] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    facts: list[dict] = field(
        default_factory=list
    )

    derived_metrics: list[dict] = field(
        default_factory=list
    )


class ReasoningEngine:

    def reason(
        self,
        task: AnalysisTask,
        analysis: AnalysisResult,
    ) -> ReasoningResult:

        if not analysis.evidence:
            return ReasoningResult(
                answer=(
                    "Недостаточно проверенных "
                    "данных для ответа."
                ),
                confidence=0.0,
                verified=False,
                warnings=[
                    "No evidence available."
                ],
            )

        citations = [
            item.url
            for item in analysis.evidence
            if item.url
        ]

        if not analysis.verified:
            answer = (
                "Я нашёл данные по запросу, "
                "но не могу считать их "
                "достаточно независимо "
                "подтверждёнными."
            )
        else:
            answer = (
                "Данные прошли независимую "
                "проверку источников."
            )

        return ReasoningResult(
            answer=answer,
            confidence=analysis.confidence,
            verified=analysis.verified,
            citations=citations,
            warnings=analysis.warnings,
        )
