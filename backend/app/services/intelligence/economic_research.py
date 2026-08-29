from app.services.data_sources.economic.provider import (
    EconomicDataProvider,
    EconomicDataRequest,
)
from app.services.intelligence.evidence import Evidence
from app.services.intelligence.economic_evidence import (
    economic_data_to_evidence,
)


ECONOMIC_INDICATORS = (
    "inflation",
    "interest_rate",
    "gdp",
    "unemployment",
    "currency",
)


async def collect_economic_evidence(
    provider: EconomicDataProvider,
    country: str,
) -> list[Evidence]:

    evidence: list[Evidence] = []

    for indicator in ECONOMIC_INDICATORS:

        response = await provider.get_data(
            EconomicDataRequest(
                indicator=indicator,
                country=country,
            )
        )

        if not response.success:
            continue

        evidence.extend(
            economic_data_to_evidence(
                response.data
            )
        )

    return evidence
