from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CFOImpact:
    metric: str
    current_value: float | None
    benchmark: float | None
    impact: str
    severity: str
    explanation: str
    recommended_action: str


class CFOImpactEngine:

    def analyze(
        self,
        evidence_pack: Any,
    ) -> list[CFOImpact]:

        impacts: list[CFOImpact] = []

        metrics = (
            evidence_pack.derived_metrics
            or {}
        )

        # ---------------------------------------------
        # LIQUIDITY / CASH RUNWAY
        # ---------------------------------------------

        runway = self._get_value(
            metrics,
            "cash_runway",
        )

        if runway is not None:

            if runway < 3:
                severity = "critical"
                impact = "negative"
                explanation = (
                    "Cash runway ниже минимального "
                    "целевого уровня в 3 месяца."
                )
                action = (
                    "Немедленно сформировать план "
                    "увеличения cash runway минимум до "
                    "3 месяцев."
                )

            elif runway < 6:
                severity = "warning"
                impact = "negative"
                explanation = (
                    "Ликвидности достаточно для "
                    "краткосрочной работы, но запас "
                    "ограничен."
                )
                action = (
                    "Увеличить ликвидный резерв и "
                    "контролировать месячный cash burn."
                )

            else:
                severity = "healthy"
                impact = "positive"
                explanation = (
                    "Компания располагает достаточным "
                    "запасом ликвидности."
                )
                action = (
                    "Сохранять резерв и направлять "
                    "избыточный cash в наиболее "
                    "эффективные направления."
                )

            impacts.append(
                CFOImpact(
                    metric="cash_runway",
                    current_value=runway,
                    benchmark=3.0,
                    impact=impact,
                    severity=severity,
                    explanation=explanation,
                    recommended_action=action,
                )
            )

        # ---------------------------------------------
        # NET MARGIN
        # ---------------------------------------------

        margin = self._get_value(
            metrics,
            "net_margin",
        )

        if margin is not None:

            if margin < 10:
                severity = "critical"
                impact = "negative"
                explanation = (
                    "Чистая маржа находится на низком "
                    "уровне и ограничивает способность "
                    "компании выдерживать финансовые шоки."
                )
                action = (
                    "Провести анализ unit economics и "
                    "сократить наиболее неэффективные "
                    "операционные расходы."
                )

            elif margin < 20:
                severity = "warning"
                impact = "neutral"
                explanation = (
                    "Маржа положительная, но запас "
                    "прочности ограничен."
                )
                action = (
                    "Контролировать рост расходов "
                    "быстрее роста выручки."
                )

            else:
                severity = "healthy"
                impact = "positive"
                explanation = (
                    "Компания демонстрирует высокий "
                    "уровень операционной прибыльности."
                )
                action = (
                    "Сохранять маржинальность при "
                    "масштабировании бизнеса."
                )

            impacts.append(
                CFOImpact(
                    metric="net_margin",
                    current_value=margin,
                    benchmark=20.0,
                    impact=impact,
                    severity=severity,
                    explanation=explanation,
                    recommended_action=action,
                )
            )

        # ---------------------------------------------
        # EXPENSE / REVENUE
        # ---------------------------------------------

        revenue = self._get_value(
            metrics,
            "revenue",
        )

        expenses = self._get_value(
            metrics,
            "expenses",
        )

        if revenue and expenses:

            expense_ratio = (
                expenses / revenue * 100
            )

            if expense_ratio > 90:
                severity = "critical"
                impact = "negative"
                explanation = (
                    "Расходы поглощают большую часть "
                    "выручки."
                )
                action = (
                    "Немедленно провести cost review "
                    "и определить расходы, которые "
                    "можно сократить без ущерба "
                    "для revenue."
                )

            elif expense_ratio > 75:
                severity = "warning"
                impact = "negative"
                explanation = (
                    "Высокая доля расходов относительно "
                    "выручки ограничивает финансовую "
                    "гибкость."
                )
                action = (
                    "Установить контроль expense-to-revenue "
                    "ratio и лимиты по основным категориям."
                )

            else:
                severity = "healthy"
                impact = "positive"
                explanation = (
                    "Расходная база находится под "
                    "относительным контролем."
                )
                action = (
                    "Сохранять текущую дисциплину расходов "
                    "при масштабировании выручки."
                )

            impacts.append(
                CFOImpact(
                    metric="expense_ratio",
                    current_value=expense_ratio,
                    benchmark=75.0,
                    impact=impact,
                    severity=severity,
                    explanation=explanation,
                    recommended_action=action,
                )
            )

        return impacts

    @staticmethod
    def _get_value(
        metrics: dict[str, float],
        metric: str,
    ) -> float | None:

        value = metrics.get(metric)

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
