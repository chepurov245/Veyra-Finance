from app.services.intelligence.evidence import Evidence
from app.services.intelligence.evidence_dedup import (
    EvidenceDeduplicator,
)
from app.services.intelligence.source_reliability import (
    SourceReliability,
)
from app.services.intelligence.verification import (
    EvidenceVerifier,
)


def make_evidence(
    claim: str,
    url: str,
    confidence: float = 0.6,
):
    return Evidence(
        claim=claim,
        source_name="test",
        source_type="web",
        url=url,
        confidence=confidence,
        source_reliability=(
            SourceReliability.MEDIUM
        ),
    )


def test_same_publisher_is_not_independent():
    evidence = [
        make_evidence(
            "Inflation is 6.13%.",
            "https://investing.com/a",
        ),
        make_evidence(
            "Inflation is 6.13%.",
            "https://investing.com/b",
        ),
    ]

    result = EvidenceVerifier().verify(
        evidence
    )

    assert result.verified is False
    assert result.confidence == 0.6


def test_republisher_is_not_independent():
    evidence = [
        make_evidence(
            "Inflation is 6.13%.",
            "https://investing.com/a",
        ),
        make_evidence(
            "Inflation is 6.13%. "
            "([investing.com]"
            "(https://investing.com/a))",
            "https://deita.ru/article/a",
        ),
    ]

    result = EvidenceVerifier().verify(
        evidence
    )

    assert result.verified is False


def test_two_independent_publishers_verify():
    evidence = [
        make_evidence(
            "Inflation is 6.13%.",
            "https://cbr.ru/a",
            confidence=0.9,
        ),
        make_evidence(
            "Inflation is 6.13%.",
            "https://interfax.ru/a",
            confidence=0.8,
        ),
    ]

    result = EvidenceVerifier().verify(
        evidence
    )

    assert result.verified is True
    assert result.confidence == 0.95


def test_cited_publishers_are_detected():
    claim = (
        "According to "
        "https://investing.com/article/a "
        "inflation is 6.13%."
    )

    publishers = (
        EvidenceDeduplicator.cited_publishers(
            claim
        )
    )

    assert "investing.com" in publishers


print("EVIDENCE REGRESSION TESTS: OK")
