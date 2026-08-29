from dataclasses import dataclass, field


@dataclass
class CFOCalculationResult:
    metrics: dict[str, float] = field(
        default_factory=dict
    )
    statuses: dict[str, str] = field(
        default_factory=dict
    )
    warnings: list[str] = field(
        default_factory=list
    )


class CFOCalculationEngine:

    @staticmethod
    def _value(
        facts: list[dict],
        metric: str,
    ) -> float | None:

        for fact in facts:
            if fact.get("metric") != metric:
                continue

            value = fact.get("value")

            if value is None:
                continue

            try:
                return float(value)
            except (TypeError, ValueError):
                continue

        return None

    def calculate(
        self,
        facts: list[dict],
    ) -> CFOCalculationResult:

        metrics: dict[str, float] = {}
        statuses: dict[str, str] = {}
        warnings: list[str] = []

        revenue = self._value(
            facts,
            "revenue",
        )

        expenses = self._value(
            facts,
            "expenses",
        )

        net_income = self._value(
            facts,
            "net_income",
        )

        cash_balance = self._value(
            facts,
            "cash_balance",
        )

        payroll = self._value(
            facts,
            "monthly_payroll",
        )

        debt = self._value(
            facts,
            "total_debt",
        )

        debt_payment = self._value(
            facts,
            "monthly_debt_payment",
        )

        # ---------------------------------------------
        # BASE METRICS
        # ---------------------------------------------

        if revenue is not None:
            metrics["revenue"] = revenue

        if expenses is not None:
            metrics["expenses"] = expenses

        if net_income is not None:
            metrics["net_income"] = net_income

        if cash_balance is not None:
            metrics["cash_balance"] = cash_balance

        # ---------------------------------------------
        # EXPENSE RATIO
        # ---------------------------------------------

        if revenue and revenue > 0 and expenses is not None:

            expense_ratio = (
                expenses / revenue * 100
            )

            metrics["expense_ratio"] = expense_ratio

        # ---------------------------------------------
        # NET MARGIN
        # ---------------------------------------------

        if revenue and revenue > 0 and net_income is not None:

            net_margin = (
                net_income / revenue * 100
            )

            metrics["net_margin"] = net_margin

            if net_margin < 0:
                statuses["profitability"] = "critical"

            elif net_margin < 10:
                statuses["profitability"] = "warning"

            elif net_margin < 20:
                statuses["profitability"] = "moderate"

            else:
                statuses["profitability"] = "healthy"

        # ---------------------------------------------
        # MONTHLY BURN
        # ---------------------------------------------

        if expenses is not None and expenses > 0:

            metrics["monthly_burn"] = expenses

        # ---------------------------------------------
        # CASH RUNWAY
        # ---------------------------------------------

        if (
            cash_balance is not None
            and expenses
            and expenses > 0
        ):

            cash_runway = (
                cash_balance / expenses
            )

            metrics["cash_runway"] = cash_runway

            if cash_runway < 1:
                statuses["liquidity"] = "critical"

            elif cash_runway < 3:
                statuses["liquidity"] = "critical"

            elif cash_runway < 6:
                statuses["liquidity"] = "warning"

            else:
                statuses["liquidity"] = "healthy"

        # ---------------------------------------------
        # BREAK-EVEN REVENUE
        # ---------------------------------------------

        if expenses is not None:

            metrics["break_even_revenue"] = (
                expenses
            )

        # ---------------------------------------------
        # PAYROLL RATIO
        # ---------------------------------------------

        if (
            payroll is not None
            and expenses
            and expenses > 0
        ):

            metrics["payroll_ratio"] = (
                payroll / expenses * 100
            )

        # ---------------------------------------------
        # DEBT / REVENUE
        # ---------------------------------------------

        if (
            debt is not None
            and revenue
            and revenue > 0
        ):

            debt_to_revenue = (
                debt / revenue * 100
            )

            metrics["debt_to_revenue"] = (
                debt_to_revenue
            )

            if debt_to_revenue > 100:
                statuses["leverage"] = "critical"

            elif debt_to_revenue > 50:
                statuses["leverage"] = "warning"

            elif debt_to_revenue > 30:
                statuses["leverage"] = "moderate"

            else:
                statuses["leverage"] = "healthy"

        # ---------------------------------------------
        # DEBT SERVICE RATIO
        # ---------------------------------------------

        if (
            debt_payment is not None
            and revenue
            and revenue > 0
        ):

            metrics["debt_service_ratio"] = (
                debt_payment / revenue * 100
            )

        # ---------------------------------------------
        # DATA QUALITY
        # ---------------------------------------------

        if revenue is None:
            warnings.append(
                "Revenue is unavailable."
            )

        if expenses is None:
            warnings.append(
                "Expenses are unavailable."
            )

        if cash_balance is None:
            warnings.append(
                "Cash balance is unavailable."
            )

        return CFOCalculationResult(
            metrics=metrics,
            statuses=statuses,
            warnings=warnings,
        )
