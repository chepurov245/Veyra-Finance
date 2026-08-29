from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FinancialAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    account_type: str = Field(min_length=1, max_length=50)
    currency: str = Field(min_length=3, max_length=10)
    balance: Decimal = Decimal("0")


class FinancialAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    name: str
    account_type: str
    currency: str
    balance: Decimal
    status: str


class FinancialTransactionCreate(BaseModel):
    account_id: int
    transaction_type: str = Field(min_length=1, max_length=30)
    amount: Decimal
    currency: str = Field(min_length=3, max_length=10)
    category: str | None = Field(default=None, max_length=100)
    description: str | None = None
    transaction_date: datetime


class FinancialTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workspace_id: int
    account_id: int
    transaction_type: str
    amount: Decimal
    currency: str
    category: str | None
    description: str | None
    transaction_date: datetime
