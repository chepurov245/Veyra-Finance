from __future__ import annotations

from decimal import Decimal


def _to_float(value) -> float:
    if isinstance(value, Decimal):
        return float(value)

    return float(value or 0)


def _round(value: float, digits: int = 2) -> float:
    return round(value, digits)


def generate_cfo_decision(analysis: dict) -> dict:
    financials = analysis.get("financials", analysis)

    revenue = _to_float(financials.get("revenue"))
    expenses = _to_float(financials.get("expenses"))
    net_income = _to_float(financials.get("net_income"))
    net_margin = _to_float(financials.get("net_margin"))
    cash_balance = _to_float(financials.get("cash_balance"))

    expense_breakdown = analysis.get("expense_breakdown", [])

    baseline = analysis.get("financial_baseline") or {}

    accounts_receivable = _to_float(
        baseline.get("accounts_receivable")
    )

    accounts_payable = _to_float(
        baseline.get("accounts_payable")
    )

    total_debt = _to_float(
        baseline.get("total_debt")
    )

    monthly_debt_payment = _to_float(
        baseline.get("monthly_debt_payment")
    )

    monthly_payroll = _to_float(
        baseline.get("monthly_payroll")
    )

    employee_count = int(
        _to_float(baseline.get("employee_count"))
    )

    risks: list[dict] = []
    opportunities: list[dict] = []
    actions: list[dict] = []

    # ---------------------------------------------------------
    # 1. FINANCIAL HEALTH
    # ---------------------------------------------------------

    if revenue <= 0:
        financial_health = "critical"
        health_message = (
            "Недостаточно данных о выручке для подтверждения "
            "финансовой устойчивости компании."
        )

    elif net_margin >= 30:
        financial_health = "strong"
        health_message = (
            "Компания демонстрирует высокую прибыльность "
            "и положительный операционный результат."
        )

    elif net_margin >= 15:
        financial_health = "stable"
        health_message = (
            "Компания прибыльна, однако необходимо контролировать "
            "структуру расходов и ликвидность."
        )

    elif net_margin >= 0:
        financial_health = "weak"
        health_message = (
            "Компания прибыльна, но запас финансовой прочности "
            "ограничен."
        )

    else:
        financial_health = "critical"
        health_message = (
            "Компания работает с отрицательной рентабельностью."
        )

    # ---------------------------------------------------------
    # 2. CASH RUNWAY
    # ---------------------------------------------------------

    runway = (
        cash_balance / expenses
        if expenses > 0
        else 0
    )

    if cash_balance <= 0 and expenses > 0:

        risks.append(
            {
                "type": "liquidity",
                "severity": "critical",
                "title": "Отсутствует cash buffer",
                "message": (
                    "Компания не имеет положительного "
                    "денежного резерва."
                ),
            }
        )

        actions.append(
            {
                "priority": "critical",
                "title": "Восстановить cash buffer",
                "action": (
                    "Сформировать резерв минимум на 3 месяца "
                    "операционных расходов."
                ),
            }
        )

    elif runway < 2:

        risks.append(
            {
                "type": "liquidity",
                "severity": "high",
                "title": "Низкий cash runway",
                "message": (
                    f"Текущий cash balance покрывает "
                    f"примерно {runway:.1f} периода расходов."
                ),
            }
        )

        actions.append(
            {
                "priority": "high",
                "title": "Увеличить ликвидный резерв",
                "action": (
                    "Целевой ориентир — минимум 3 месяца "
                    "операционных расходов."
                ),
            }
        )

    elif runway < 3:

        risks.append(
            {
                "type": "liquidity",
                "severity": "medium",
                "title": "Ограниченный cash buffer",
                "message": (
                    f"Cash balance покрывает примерно "
                    f"{runway:.1f} периода расходов."
                ),
            }
        )

    else:

        opportunities.append(
            {
                "type": "cash_position",
                "title": "Здоровая cash position",
                "message": (
                    f"Текущий cash balance покрывает "
                    f"примерно {runway:.1f} периода расходов."
                ),
            }
        )

    # ---------------------------------------------------------
    # 3. RECEIVABLES
    # ---------------------------------------------------------

    if accounts_receivable > 0 and revenue > 0:

        ar_ratio = (
            accounts_receivable / revenue
        ) * 100

        if ar_ratio >= 30:

            risks.append(
                {
                    "type": "receivables",
                    "severity": "high",
                    "title": "Высокая дебиторская задолженность",
                    "message": (
                        f"Accounts receivable составляет "
                        f"{accounts_receivable:,.2f}, "
                        f"или примерно {ar_ratio:.1f}% месячной выручки."
                    ),
                }
            )

            actions.append(
                {
                    "priority": "high",
                    "title": "Ускорить сбор дебиторки",
                    "action": (
                        "Проверить просроченные счета и сократить "
                        "DSO / срок оплаты клиентов."
                    ),
                }

            )

        elif ar_ratio >= 15:

            risks.append(
                {
                    "type": "receivables",
                    "severity": "medium",
                    "title": "Значимая дебиторская задолженность",
                    "message": (
                        f"Accounts receivable составляет "
                        f"{accounts_receivable:,.2f}."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 4. PAYABLES
    # ---------------------------------------------------------

    if accounts_payable > 0 and expenses > 0:

        ap_ratio = (
            accounts_payable / expenses
        ) * 100

        if ap_ratio >= 50:

            risks.append(
                {
                    "type": "payables",
                    "severity": "high",
                    "title": "Высокая кредиторская задолженность",
                    "message": (
                        f"Accounts payable составляет "
                        f"{accounts_payable:,.2f}, "
                        f"или {ap_ratio:.1f}% месячных расходов."
                    ),
                }
            )

            actions.append(
                {
                    "priority": "high",
                    "title": "Контролировать обязательства",
                    "action": (
                        "Проверить сроки оплаты поставщикам "
                        "и будущие cash outflows."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 5. DEBT
    # ---------------------------------------------------------

    if total_debt > 0:

        debt_to_revenue = (
            total_debt / revenue
        ) * 100 if revenue > 0 else 0

        if debt_to_revenue >= 50:

            risks.append(
                {
                    "type": "debt",
                    "severity": "high",
                    "title": "Высокая долговая нагрузка",
                    "message": (
                        f"Total debt составляет "
                        f"{total_debt:,.2f}, "
                        f"или {debt_to_revenue:.1f}% "
                        "месячной выручки."
                    ),
                }
            )

            actions.append(
                {
                    "priority": "high",
                    "title": "Контролировать долговую нагрузку",
                    "action": (
                        "Отслеживать debt balance, debt service "
                        "и способность компании обслуживать долг."
                    ),
                }
            )

        elif debt_to_revenue >= 25:

            risks.append(
                {
                    "type": "debt",
                    "severity": "medium",
                    "title": "Умеренная долговая нагрузка",
                    "message": (
                        f"Total debt составляет "
                        f"{total_debt:,.2f}."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 6. DEBT SERVICE
    # ---------------------------------------------------------

    if monthly_debt_payment > 0 and revenue > 0:

        debt_service_ratio = (
            monthly_debt_payment / revenue
        ) * 100

        if debt_service_ratio >= 10:

            risks.append(
                {
                    "type": "debt_service",
                    "severity": "medium",
                    "title": "Высокая долговая нагрузка на cash flow",
                    "message": (
                        f"Ежемесячные платежи по долгу "
                        f"{monthly_debt_payment:,.2f}, "
                        f"что составляет "
                        f"{debt_service_ratio:.1f}% выручки."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 7. PAYROLL
    # ---------------------------------------------------------

    if monthly_payroll > 0 and expenses > 0:

        payroll_ratio = (
            monthly_payroll / expenses
        ) * 100

        if payroll_ratio >= 50:

            risks.append(
                {
                    "type": "payroll",
                    "severity": "medium",
                    "title": "Высокая доля payroll",
                    "message": (
                        f"Payroll составляет "
                        f"{payroll_ratio:.1f}% всех расходов."
                    ),
                }
            )

            actions.append(
                {
                    "priority": "medium",
                    "title": "Контролировать payroll",
                    "action": (
                        "Отслеживать payroll как отдельный "
                        "CFO KPI и оценивать его относительно выручки."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 8. COST CONCENTRATION
    # ---------------------------------------------------------

    if expense_breakdown:

        largest_expense = max(
            expense_breakdown,
            key=lambda item: _to_float(
                item.get("percentage")
            ),
        )

        largest_percentage = _to_float(
            largest_expense.get("percentage")
        )

        largest_category = largest_expense.get(
            "category",
            "UNKNOWN",
        )

        if largest_percentage >= 50:

            risks.append(
                {
                    "type": "cost_concentration",
                    "severity": "medium",
                    "title": "Высокая концентрация расходов",
                    "message": (
                        f"{largest_category} составляет "
                        f"{largest_percentage:.2f}% "
                        "всех расходов."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 9. PROFITABILITY
    # ---------------------------------------------------------

    if revenue > 0 and net_income > 0:

        opportunities.append(
            {
                "type": "profitability",
                "title": "Положительная прибыльность",
                "message": (
                    f"Компания генерирует "
                    f"{net_income:,.2f} чистой прибыли "
                    f"при марже {net_margin:.2f}%."
                ),
            }
        )

    # ---------------------------------------------------------
    # 10. BREAK-EVEN
    # ---------------------------------------------------------

    break_even_revenue = expenses

    if revenue > 0:

        safety_margin = (
            (revenue - break_even_revenue)
            / revenue
        ) * 100

        if safety_margin > 30:

            opportunities.append(
                {
                    "type": "break_even",
                    "title": "Высокий запас относительно break-even",
                    "message": (
                        f"Выручка превышает базовые расходы "
                        f"на {safety_margin:.1f}%."
                    ),
                }
            )

    # ---------------------------------------------------------
    # 11. HEADCOUNT
    # ---------------------------------------------------------

    payroll_per_employee = (
        monthly_payroll / employee_count
        if employee_count > 0
        else 0
    )

    # ---------------------------------------------------------
    # 12. GENERAL ACTION
    # ---------------------------------------------------------

    if financial_health in {"strong", "stable"}:

        actions.append(
            {
                "priority": "high",
                "title": "Сохранить контроль маржи",
                "action": (
                    "Регулярно отслеживать revenue, expenses, "
                    "net margin и cash flow."
                ),
            }
        )

    # ---------------------------------------------------------
    # 13. HEALTH SCORE
    # ---------------------------------------------------------

    score = 100

    for risk in risks:

        severity = risk["severity"]

        if severity == "critical":
            score -= 30

        elif severity == "high":
            score -= 20

        elif severity == "medium":
            score -= 10

        else:
            score -= 5

    score = max(0, min(100, score))

    # ---------------------------------------------------------
    # 14. MAIN RISK
    # ---------------------------------------------------------

    severity_order = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }

    main_risk = None

    if risks:
        main_risk = max(
            risks,
            key=lambda risk: severity_order.get(
                risk["severity"],
                0,
            ),
        )

    return {
        "financial_health": {
            "status": financial_health,
            "score": score,
            "message": health_message,
        },

        "key_metrics": {
            "revenue": _round(revenue),
            "expenses": _round(expenses),
            "net_income": _round(net_income),
            "net_margin": _round(net_margin),
            "cash_balance": _round(cash_balance),
            "cash_runway_periods": _round(runway),
            "accounts_receivable": _round(
                accounts_receivable
            ),
            "accounts_payable": _round(
                accounts_payable
            ),
            "total_debt": _round(total_debt),
            "monthly_debt_payment": _round(
                monthly_debt_payment
            ),
            "monthly_payroll": _round(
                monthly_payroll
            ),
            "employee_count": employee_count,
            "payroll_per_employee": _round(
                payroll_per_employee
            ),
            "break_even_revenue": _round(
                break_even_revenue
            ),
        },

        "main_risk": main_risk,

        "risks": risks,

        "opportunities": opportunities,

        "recommended_actions": actions,
    }
