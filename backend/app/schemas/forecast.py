from decimal import Decimal

from pydantic import BaseModel


class ForecastPeriod(BaseModel):
    period: int
    revenue: Decimal
    expenses: Decimal
    net_income: Decimal
    net_margin: Decimal
    cash_balance: Decimal
    cash_runway_periods: Decimal


class ForecastAssumptions(BaseModel):
    revenue_growth_pct: Decimal
    expense_growth_pct: Decimal


class ForecastScenario(BaseModel):
    assumptions: ForecastAssumptions
    periods: list[ForecastPeriod]


class FinancialForecastResponse(BaseModel):
    base_metrics: dict[str, Decimal]
    periods: int
    scenarios: dict[str, ForecastScenario]
