from dataclasses import dataclass, field
from typing import Any

from app.services.intelligence.evidence import Evidence


@dataclass
class ResearchResult:
    query: str
    evidence: list[Evidence] = field(
        default_factory=list
    )
    raw_data: list[Any] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )

    def add_evidence(self, item: Evidence) -> None:
        self.evidence.append(item)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)
