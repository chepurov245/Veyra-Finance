from app.services.data_sources.economic.provider import (
    EconomicDataPoint,
)
from app.services.intelligence.evidence import Evidence
from app.services.intelligence.source_reliability import (
    classify_source,
)


def economic_data_to_evidence(
    data: list[EconomicDataPoint],
) -> list[Evidence]:

    evidence: list[Evidence] = []

    for item in data:

        claim = (
            f"{item.indicator}: "
            f"{item.value}"
        )

        if item.unit:
            claim += f" {item.unit}"

        if item.country:
            claim += (
                f" в {item.country}"
            )

        if item.period:
            claim += (
                f" за период {item.period}"
            )

        reliability = classify_source(
            item.url
            or ""
        )

        if reliability.value >= 4:
            confidence = 0.90
        elif reliability.value >= 3:
            confidence = 0.80
        elif reliability.value >= 2:
            confidence = 0.60
        else:
            confidence = 0.30

        evidence.append(
            Evidence(
                claim=claim,
                source_name=(
                    item.source
                    or "Economic data provider"
                ),
                source_type="economic",
                url=item.url,
                confidence=confidence,
                source_reliability=reliability,
                metadata={
                    "indicator": item.indicator,
                    "value": item.value,
                    "unit": item.unit,
                    "country": item.country,
                    "period": item.period,
                    "economic_data": True,
                },
            )
        )

    return evidence
