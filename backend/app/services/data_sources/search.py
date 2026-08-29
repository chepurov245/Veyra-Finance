from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchRequest:
    query: str
    country: str | None = None
    language: str | None = None
    max_results: int = 10


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    published_at: str | None = None
    content: str = ""


@dataclass
class SearchResponse:
    provider: str
    success: bool
    results: list[SearchResult] = field(default_factory=list)
    error: str | None = None


class SearchProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def search(
        self,
        request: SearchRequest,
    ) -> SearchResponse:
        raise NotImplementedError
