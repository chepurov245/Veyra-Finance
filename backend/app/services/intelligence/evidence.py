from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.services.intelligence.source_reliability import (
    SourceReliability,
)


@dataclass(frozen=True)
class Evidence:
    claim: str
    source_name: str
    source_type: str
    url: str | None = None
    published_at: datetime | None = None
    retrieved_at: datetime = field(
        default_factory=datetime.utcnow
    )
    confidence: float = 1.0
    source_reliability: SourceReliability = (
        SourceReliability.UNKNOWN
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.claim.strip():
            raise ValueError(
                "Evidence claim cannot be empty."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "Evidence confidence must be between 0 and 1."
            )
