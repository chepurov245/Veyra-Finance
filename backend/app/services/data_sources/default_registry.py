from app.services.data_sources.openai_search import (
    OpenAIWebSearchProvider,
)
from app.services.data_sources.search_registry import (
    SearchProviderRegistry,
)


def build_search_registry() -> SearchProviderRegistry:
    registry = SearchProviderRegistry()

    registry.register(
        OpenAIWebSearchProvider()
    )

    return registry
