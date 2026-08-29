from app.services.data_sources.base import DataSource


class DataSourceRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, DataSource] = {}

    def register(self, source: DataSource) -> None:
        if source.name in self._sources:
            raise ValueError(
                f"Data source already registered: {source.name}"
            )

        self._sources[source.name] = source

    def get(self, name: str) -> DataSource:
        try:
            return self._sources[name]
        except KeyError as exc:
            raise KeyError(
                f"Unknown data source: {name}"
            ) from exc

    def list(self) -> list[DataSource]:
        return list(self._sources.values())
