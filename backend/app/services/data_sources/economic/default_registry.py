from app.services.data_sources.economic.openai_economic import (
    OpenAIEconomicDataProvider,
)
from app.services.data_sources.economic.registry import (
    EconomicDataProviderRegistry,
)


def build_economic_registry(
) -> EconomicDataProviderRegistry:

    registry = EconomicDataProviderRegistry()

    registry.register(
        OpenAIEconomicDataProvider()
    )

    return registry
