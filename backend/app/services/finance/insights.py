from decimal import Decimal


def generate_cfo_insights(
    analysis: dict,
    comparison: dict | None = None,
) -> list[dict]:
    insights: list[dict] = []

    revenue = Decimal(str(analysis["revenue"]))
    expenses = Decimal(str(analysis["expenses"]))
    net_income = Decimal(str(analysis["net_income"]))
    net_margin = Decimal(str(analysis["net_margin"]))

    if revenue > 0 and net_income > 0:
        insights.append(
            {
                "type": "positive",
                "severity": "low",
                "title": "Positive profitability",
                "message": (
                    f"Net income is {net_income:.2f} "
                    f"with a net margin of {net_margin:.2f}%."
                ),
            }
        )

    if revenue > 0 and net_income < 0:
        insights.append(
            {
                "type": "risk",
                "severity": "high",
                "title": "Negative profitability",
                "message": (
                    f"The company is currently loss-making "
                    f"with a net loss of {abs(net_income):.2f}."
                ),
            }
        )

    for item in analysis.get("expense_breakdown", []):
        percentage = Decimal(str(item["percentage"]))

        if percentage >= 50:
            insights.append(
                {
                    "type": "cost_concentration",
                    "severity": "medium",
                    "title": "High expense concentration",
                    "message": (
                        f'{item["category"]} represents '
                        f"{percentage:.2f}% of total expenses."
                    ),
                }
            )

    if comparison:
        changes = comparison.get("changes", {})

        revenue_change = changes.get("revenue_change_pct")
        expense_change = changes.get("expenses_change_pct")
        margin_change = changes.get("net_margin_change_pp")

        if revenue_change is not None:
            revenue_change = Decimal(str(revenue_change))

            if revenue_change < 0:
                insights.append(
                    {
                        "type": "risk",
                        "severity": "medium",
                        "title": "Revenue decline",
                        "message": (
                            f"Revenue decreased by "
                            f"{abs(revenue_change):.2f}% "
                            f"versus the previous period."
                        ),
                    }
                )

        if expense_change is not None:
            expense_change = Decimal(str(expense_change))

            if expense_change > 20:
                insights.append(
                    {
                        "type": "risk",
                        "severity": "medium",
                        "title": "Expense acceleration",
                        "message": (
                            f"Expenses increased by "
                            f"{expense_change:.2f}% "
                            f"versus the previous period."
                        ),
                    }
                )

        if margin_change is not None:
            margin_change = Decimal(str(margin_change))

            if margin_change < 0:
                insights.append(
                    {
                        "type": "margin_pressure",
                        "severity": "medium",
                        "title": "Margin pressure",
                        "message": (
                            f"Net margin decreased by "
                            f"{abs(margin_change):.2f} percentage points."
                        ),
                    }
                )

    return insights
