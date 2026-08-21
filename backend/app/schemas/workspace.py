from typing import Literal

from pydantic import BaseModel, Field


WorkspaceType = Literal["PERSONAL", "BUSINESS"]


class WorkspaceCreate(BaseModel):
    type: WorkspaceType
    name: str = Field(min_length=1, max_length=200)
    base_currency: str = Field(
        default="RUB",
        min_length=3,
        max_length=10,
    )
    country: str | None = Field(
        default=None,
        max_length=100,
    )


class WorkspaceResponse(BaseModel):
    id: int
    owner_id: int
    type: WorkspaceType
    name: str
    base_currency: str
    country: str | None
    status: str

    model_config = {
        "from_attributes": True,
    }
