from app.services.data_sources.search import SearchProvider


class SearchProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, SearchProvider] = {}

    def register(self, provider: SearchProvider) -> None:
        if provider.name in self._providers:
            raise ValueError(
                f"Search provider already registered: {provider.name}"
            )

        self._providers[provider.name] = provider

    def get(self, name: str) -> SearchProvider:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown search provider: {name}"
            ) from exc

    def list(self) -> list[SearchProvider]:
        return list(self._providers.values())
