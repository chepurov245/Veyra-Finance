from app.services.data_sources.economic.provider import (
    EconomicDataProvider,
)


class EconomicDataProviderRegistry:

    def __init__(self) -> None:
        self._providers: dict[
            str,
            EconomicDataProvider,
        ] = {}

    def register(
        self,
        provider: EconomicDataProvider,
    ) -> None:

        if provider.name in self._providers:
            raise ValueError(
                f"Economic provider already registered: "
                f"{provider.name}"
            )

        self._providers[
            provider.name
        ] = provider

    def get(
        self,
        name: str,
    ) -> EconomicDataProvider:

        try:
            return self._providers[name]

        except KeyError as exc:
            raise KeyError(
                f"Unknown economic provider: {name}"
            ) from exc

    def list(
        self,
    ) -> list[EconomicDataProvider]:

        return list(
            self._providers.values()
        )
