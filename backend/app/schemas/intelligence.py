from pydantic import BaseModel, Field


class IntelligenceRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )
    has_workspace: bool = False


class IntelligenceCitation(BaseModel):
    url: str
    title: str | None = None


class IntelligenceFact(BaseModel):
    claim: str
    value: float | None = None
    unit: str | None = None
    period: str | None = None
    verified: bool = False


class IntelligenceResponse(BaseModel):
    answer: str
    verified: bool
    confidence: float
    citations: list[IntelligenceCitation] = Field(
        default_factory=list
    )
    warnings: list[str] = Field(
        default_factory=list
    )
    facts: list[IntelligenceFact] = Field(
        default_factory=list
    )
