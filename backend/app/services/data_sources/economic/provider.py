from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EconomicDataRequest:
    indicator: str
    country: str | None = None
    start_date: str | None = None
    end_date: str | None = None


@dataclass(frozen=True)
class EconomicDataPoint:
    indicator: str
    value: float
    unit: str | None = None
    country: str | None = None
    period: str | None = None
    source: str = ""
    url: str | None = None


@dataclass
class EconomicDataResponse:
    provider: str
    success: bool
    data: list[EconomicDataPoint] = field(
        default_factory=list
    )
    error: str | None = None


class EconomicDataProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_data(
        self,
        request: EconomicDataRequest,
    ) -> EconomicDataResponse:
        raise NotImplementedError
