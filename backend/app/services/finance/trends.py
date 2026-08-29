from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import FinancialTransaction


def _percent_change(
    current: Decimal,
    previous: Decimal,
) -> Decimal | None:
    if previous == 0:
        return None

    return (
        (current - previous) / abs(previous)
    * Decimal("100")
    ).quantize(Decimal("0.01"))


def _analyze_period(
    transactions: list[FinancialTransaction],
) -> dict:
    revenue = Decimal("0")
    expenses = Decimal("0")

    for transaction in transactions:
        if transaction.transaction_type == "INCOME":
            revenue += transaction.amount

        elif transaction.transaction_type == "EXPENSE":
            expenses += transaction.amount

    net_income = revenue - expenses

    net_margin = (
        (net_income / revenue) * Decimal("100")
        if revenue > 0
        else Decimal("0")
    )

    return {
        "revenue": revenue.quantize(Decimal("0.01")),
        "expenses": expenses.quantize(Decimal("0.01")),
        "net_income": net_income.quantize(Decimal("0.01")),
        "net_margin": net_margin.quantize(Decimal("0.01")),
        "cash_inflow": revenue.quantize(Decimal("0.01")),
        "cash_outflow": expenses.quantize(Decimal("0.01")),
        "net_cash_flow": (
            revenue - expenses
        ).quantize(Decimal("0.01")),
    }


def analyze_financial_trends(
    db: Session,
    workspace_id: int,
    periods: int = 6,
    period_days: int = 30,
    end_date: datetime | None = None,
) -> dict:
    if periods < 1:
        raise ValueError(
            "Periods must be at least 1."
        )

    if periods > 24:
        raise ValueError(
            "Periods cannot exceed 24."
        )

    if period_days < 1:
        raise ValueError(
            "Period days must be at least 1."
        )

    if period_days > 366:
        raise ValueError(
            "Period days cannot exceed 366."
        )

    if end_date is None:
        end_date = datetime.now()

    query = (
        select(FinancialTransaction)
        .where(
            FinancialTransaction.workspace_id == workspace_id
        )
        .order_by(
            FinancialTransaction.transaction_date
        )
    )

    all_transactions = list(db.scalars(query))

    results = []

    for index in range(periods - 1, -1, -1):
        period_end = (
            end_date
            - timedelta(days=index * period_days)
        )

        period_start = (
            period_end
            - timedelta(days=period_days)
            + timedelta(seconds=1)
        )

        transactions = [
            transaction
            for transaction in all_transactions
            if (
                period_start
                <= transaction.transaction_date
                <= period_end
            )
        ]

        metrics = _analyze_period(
            transactions
        )

        results.append(
            {
                "period": len(results) + 1,
                "start": period_start,
                "end": period_end,
                **metrics,
            }
        )

    for index, current in enumerate(results):
        if index == 0:
            current["changes"] = {
                "revenue_change_pct": None,
                "expenses_change_pct": None,
                "net_income_change_pct": None,
                "net_margin_change_pp": None,
            }
            continue

        previous = results[index - 1]

        current["changes"] = {
            "revenue_change_pct": _percent_change(
                current["revenue"],
                previous["revenue"],
            ),
            "expenses_change_pct": _percent_change(
                current["expenses"],
                previous["expenses"],
            ),
            "net_income_change_pct": _percent_change(
                current["net_income"],
                previous["net_income"],
            ),
            "net_margin_change_pp": (
                current["net_margin"]
                - previous["net_margin"]
            ).quantize(Decimal("0.01")),
        }

    return {
        "workspace_id": workspace_id,
        "periods": periods,
        "period_days": period_days,
        "trend": results,
    }
