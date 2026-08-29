from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance import FinancialAccount, FinancialTransaction


def analyze_workspace_finances(
    db: Session,
    workspace_id: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    query = (
        select(FinancialTransaction)
        .where(
            FinancialTransaction.workspace_id == workspace_id
        )
        .order_by(FinancialTransaction.transaction_date)
    )

    if start_date is not None:
        query = query.where(
            FinancialTransaction.transaction_date >= start_date
        )

    if end_date is not None:
        query = query.where(
            FinancialTransaction.transaction_date <= end_date
        )

    transactions = list(db.scalars(query))

    revenue = Decimal("0")
    expenses = Decimal("0")

    expense_by_category: dict[str, Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    income_by_category: dict[str, Decimal] = defaultdict(
        lambda: Decimal("0")
    )

    for transaction in transactions:
        if transaction.transaction_type == "INCOME":
            revenue += transaction.amount

            category = transaction.category or "UNCATEGORIZED"
            income_by_category[category] += transaction.amount

        elif transaction.transaction_type == "EXPENSE":
            expenses += transaction.amount

            category = transaction.category or "UNCATEGORIZED"
            expense_by_category[category] += transaction.amount

    net_income = revenue - expenses

    cash_inflow = revenue
    cash_outflow = expenses
    net_cash_flow = cash_inflow - cash_outflow

    net_margin = (
        (net_income / revenue) * Decimal("100")
        if revenue > 0
        else Decimal("0")
    )

    expense_breakdown = [
        {
            "category": category,
            "amount": amount,
            "percentage": (
                (amount / expenses) * Decimal("100")
                if expenses > 0
                else Decimal("0")
            ),
        }
        for category, amount in sorted(
            expense_by_category.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    income_breakdown = [
        {
            "category": category,
            "amount": amount,
            "percentage": (
                (amount / revenue) * Decimal("100")
                if revenue > 0
                else Decimal("0")
            ),
        }
        for category, amount in sorted(
            income_by_category.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    return {
        "workspace_id": workspace_id,
        "transaction_count": len(transactions),
        "revenue": revenue,
        "expenses": expenses,
        "net_income": net_income,
        "net_margin": net_margin,
        "cash_inflow": cash_inflow,
        "cash_outflow": cash_outflow,
        "net_cash_flow": net_cash_flow,
        "income_breakdown": income_breakdown,
        "expense_breakdown": expense_breakdown,
    }



def get_workspace_cash_balance(
    db: Session,
    workspace_id: int,
) -> Decimal:
    accounts = list(
        db.scalars(
            select(FinancialAccount)
            .where(
                FinancialAccount.workspace_id == workspace_id,
                FinancialAccount.status == "active",
            )
        )
    )

    return sum(
        (account.balance for account in accounts),
        Decimal("0"),
    )



def compare_financial_periods(
    current: dict,
    previous: dict,
) -> dict:
    def percentage_change(
        current_value: Decimal,
        previous_value: Decimal,
    ) -> Decimal | None:
        if previous_value == 0:
            return None

        return (
            (current_value - previous_value)
            / abs(previous_value)
        ) * Decimal("100")

    return {
        "revenue_change_pct": percentage_change(
            current["revenue"],
            previous["revenue"],
        ),
        "expenses_change_pct": percentage_change(
            current["expenses"],
            previous["expenses"],
        ),
        "net_income_change_pct": percentage_change(
            current["net_income"],
            previous["net_income"],
        ),
        "net_margin_change_pp": (
            current["net_margin"] - previous["net_margin"]
        ),
    }
