from __future__ import annotations

from decimal import Decimal


SCENARIOS = {
    "conservative": {
        "revenue_growth": Decimal("-0.10"),
        "expense_growth": Decimal("0.10"),
    },
    "base": {
        "revenue_growth": Decimal("0.00"),
        "expense_growth": Decimal("0.00"),
    },
    "optimistic": {
        "revenue_growth": Decimal("0.10"),
        "expense_growth": Decimal("-0.05"),
    },
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _percent(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _forecast_period(
    revenue: Decimal,
    expenses: Decimal,
    cash_balance: Decimal,
    revenue_growth: Decimal,
    expense_growth: Decimal,
) -> dict:
    forecast_revenue = revenue * (
        Decimal("1") + revenue_growth
    )

    forecast_expenses = expenses * (
        Decimal("1") + expense_growth
    )

    forecast_net_income = (
        forecast_revenue - forecast_expenses
    )

    forecast_margin = (
        (forecast_net_income / forecast_revenue)
        * Decimal("100")
        if forecast_revenue > 0
        else Decimal("0")
    )

    forecast_cash_balance = (
        cash_balance + forecast_net_income
    )

    runway = (
        forecast_cash_balance / forecast_expenses
        if forecast_expenses > 0
        else Decimal("0")
    )

    return {
        "revenue": _money(forecast_revenue),
        "expenses": _money(forecast_expenses),
        "net_income": _money(forecast_net_income),
        "net_margin": _percent(forecast_margin),
        "cash_balance": _money(forecast_cash_balance),
        "cash_runway_periods": _percent(runway),
    }


def generate_financial_forecast(
    analysis: dict,
    periods: int = 3,
) -> dict:
    if periods < 1:
        raise ValueError(
            "Forecast periods must be at least 1."
        )

    if periods > 12:
        raise ValueError(
            "Forecast periods cannot exceed 12."
        )

    revenue = Decimal(
        str(analysis.get("revenue", 0))
    )

    expenses = Decimal(
        str(analysis.get("expenses", 0))
    )

    cash_balance = Decimal(
        str(analysis.get("cash_balance", 0))
    )

    scenarios = {}

    for scenario_name, assumptions in SCENARIOS.items():
        scenario_periods = []

        scenario_cash = cash_balance

        for period in range(1, periods + 1):
            forecast = _forecast_period(
                revenue=revenue,
                expenses=expenses,
                cash_balance=scenario_cash,
                revenue_growth=assumptions[
                    "revenue_growth"
                ],
                expense_growth=assumptions[
                    "expense_growth"
                ],
            )

            scenario_cash = forecast["cash_balance"]

            scenario_periods.append(
                {
                    "period": period,
                    **forecast,
                }
            )

        scenarios[scenario_name] = {
            "assumptions": {
                "revenue_growth_pct": _percent(
                    assumptions["revenue_growth"]
                    * Decimal("100")
                ),
                "expense_growth_pct": _percent(
                    assumptions["expense_growth"]
                    * Decimal("100")
                ),
            },
            "periods": scenario_periods,
        }

    return {
        "base_metrics": {
            "revenue": revenue,
            "expenses": expenses,
            "cash_balance": cash_balance,
        },
        "periods": periods,
        "scenarios": scenarios,
    }
