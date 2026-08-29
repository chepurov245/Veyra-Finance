from decimal import Decimal

from pydantic import BaseModel, Field


class CompanyFinancialProfileCreate(BaseModel):
    annual_revenue: Decimal | None = Field(
        default=None,
        ge=0,
    )

    monthly_revenue: Decimal | None = Field(
        default=None,
        ge=0,
    )

    monthly_expenses: Decimal | None = Field(
        default=None,
        ge=0,
    )

    monthly_payroll: Decimal | None = Field(
        default=None,
        ge=0,
    )

    monthly_marketing: Decimal | None = Field(
        default=None,
        ge=0,
    )

    monthly_software: Decimal | None = Field(
        default=None,
        ge=0,
    )

    cash_balance: Decimal | None = Field(
        default=None,
        ge=0,
    )

    accounts_receivable: Decimal | None = Field(
        default=None,
        ge=0,
    )

    accounts_payable: Decimal | None = Field(
        default=None,
        ge=0,
    )

    total_debt: Decimal | None = Field(
        default=None,
        ge=0,
    )

    monthly_debt_payment: Decimal | None = Field(
        default=None,
        ge=0,
    )

    employee_count: int | None = Field(
        default=None,
        ge=0,
    )

    fiscal_year_start: str | None = Field(
        default=None,
        max_length=10,
    )


class CompanyFinancialProfileResponse(
    CompanyFinancialProfileCreate
):
    id: int
    company_id: int
    data_source: str

    model_config = {
        "from_attributes": True,
    }
