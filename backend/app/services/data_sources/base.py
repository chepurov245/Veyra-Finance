from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class DataRequest:
    query: str
    country: str | None = None
    asset: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataPoint:
    timestamp: datetime | None
    value: float | None
    metric: str
    unit: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DataResult:
    source: str
    success: bool
    data: list[DataPoint] = field(default_factory=list)
    raw: Any = None
    error: str | None = None


class DataSource(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def source_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def fetch(self, request: DataRequest) -> DataResult:
        raise NotImplementedError
