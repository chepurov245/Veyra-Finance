from dataclasses import dataclass, field

from app.services.intelligence.evidence import Evidence
from app.services.intelligence.evidence_dedup import (
    EvidenceDeduplicator,
)
from app.services.intelligence.task_types import TaskDomain
from app.services.intelligence.source_ranking import (
    SourceRanker,
)


@dataclass
class VerificationResult:
    verified: bool
    confidence: float
    evidence: list[Evidence] = field(
        default_factory=list
    )
    supporting_evidence: list[Evidence] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )


class EvidenceVerifier:

    def __init__(self) -> None:
        self.source_ranker = SourceRanker()

    def verify(
        self,
        evidence: list[Evidence],
        domain: TaskDomain | None = None,
    ) -> VerificationResult:

        if not evidence:
            return VerificationResult(
                verified=False,
                confidence=0.0,
                warnings=[
                    "No evidence available."
                ],
            )

        groups = EvidenceDeduplicator.group(
            evidence
        )

        if not groups:
            return VerificationResult(
                verified=False,
                confidence=0.0,
                evidence=evidence,
                warnings=[
                    "No evidence groups available."
                ],
            )

        best_group = max(
            groups,
            key=lambda group: max(
                item.confidence
                for item in group.evidence
            ),
        )

        independent_evidence = [
            item
            for item in best_group.evidence
            if EvidenceDeduplicator.is_independent(
                item,
                best_group.evidence,
            )
        ]

        # -------------------------------------------------
        # Source quality ranking
        # -------------------------------------------------

        ranked_evidence = []

        for item in independent_evidence:
            source_score = self.source_ranker.rank(
                url=item.url,
                domain=domain,
            )

            ranked_evidence.append(
                (
                    item,
                    source_score,
                )
            )

        # -------------------------------------------------
        # Publisher uniqueness
        # -------------------------------------------------

        publishers = {
            EvidenceDeduplicator.publisher(
                item.url
            )
            for item in independent_evidence
        }

        publishers.discard("unknown")

        # -------------------------------------------------
        # High-quality independent sources
        # -------------------------------------------------

        high_quality_sources = [
            item
            for item, score in ranked_evidence
            if score.tier <= 3
            and item.confidence >= 0.70
        ]

        high_quality_publishers = {
            EvidenceDeduplicator.publisher(
                item.url
            )
            for item in high_quality_sources
        }

        high_quality_publishers.discard("unknown")

        # -------------------------------------------------
        # Verification decision
        # -------------------------------------------------

        if len(high_quality_publishers) >= 2:

            verified = True

            quality_confidence = max(
                item.confidence
                for item in high_quality_sources
            )

            verified_count_bonus = min(
                0.10,
                0.05 * (
                    len(high_quality_publishers) - 1
                ),
            )

            confidence = min(
                0.98,
                quality_confidence
                + verified_count_bonus,
            )

            warnings = []

        elif len(publishers) >= 2:

            # Two independent publishers exist,
            # but their source quality is not strong enough
            # for full verification.

            verified = False

            confidence = max(
                item.confidence
                for item in independent_evidence
            )

            warnings = [
                "Multiple independent sources exist, "
                "but source quality is insufficient "
                "for strong verification."
            ]

        else:

            verified = False

            confidence = max(
                item.confidence
                for item in best_group.evidence
            )

            warnings = [
                "Only one independent publisher "
                "supports this evidence."
            ]

        return VerificationResult(
            verified=verified,
            confidence=confidence,
            evidence=evidence,
            supporting_evidence=(
                best_group.evidence
            ),
            warnings=warnings,
        )
