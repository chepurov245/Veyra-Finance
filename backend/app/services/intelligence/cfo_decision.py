from dataclasses import dataclass


@dataclass(frozen=True)
class CFODecision:
    priority: int
    category: str
    severity: str
    decision: str
    reason: str
    expected_impact: str
    recommended_action: str


class CFODecisionEngine:

    SEVERITY_WEIGHT = {
        "critical": 100,
        "warning": 70,
        "moderate": 40,
        "healthy": 10,
    }

    def analyze(
        self,
        derived_metrics: dict[str, float],
        cfo_statuses: dict[str, str],
        external_impacts: list[dict],
    ) -> list[CFODecision]:

        decisions: list[CFODecision] = []

        # ---------------------------------------------
        # 1. LIQUIDITY
        # ---------------------------------------------

        runway = derived_metrics.get(
            "cash_runway"
        )

        liquidity_status = cfo_statuses.get(
            "liquidity"
        )

        if runway is not None:

            if runway < 2:

                decisions.append(
                    CFODecision(
                        priority=1,
                        category="liquidity",
                        severity="critical",
                        decision=(
                            "Немедленно увеличить "
                            "cash runway."
                        ),
                        reason=(
                            f"Текущий runway составляет "
                            f"{runway:.1f} месяца."
                        ),
                        expected_impact=(
                            "Снижение риска кассового "
                            "разрыва и повышение "
                            "финансовой устойчивости."
                        ),
                        recommended_action=(
                            "Сформировать 13-недельный "
                            "cash-flow forecast, "
                            "заморозить некритичные "
                            "расходы и определить "
                            "источники дополнительной "
                            "ликвидности."
                        ),
                    )
                )

            elif runway < 3:

                decisions.append(
                    CFODecision(
                        priority=2,
                        category="liquidity",
                        severity="warning",
                        decision=(
                            "Увеличить запас ликвидности "
                            "до безопасного уровня."
                        ),
                        reason=(
                            f"Runway составляет "
                            f"{runway:.1f} месяца."
                        ),
                        expected_impact=(
                            "Снижение вероятности "
                            "финансового стресса."
                        ),
                        recommended_action=(
                            "Сократить необязательные "
                            "расходы и увеличить "
                            "ликвидный резерв."
                        ),
                    )
                )

        # ---------------------------------------------
        # 2. PROFITABILITY
        # ---------------------------------------------

        margin = derived_metrics.get(
            "net_margin"
        )

        if margin is not None:

            if margin < 0:

                decisions.append(
                    CFODecision(
                        priority=1,
                        category="profitability",
                        severity="critical",
                        decision=(
                            "Восстановить "
                            "положительную прибыльность."
                        ),
                        reason=(
                            f"Net margin составляет "
                            f"{margin:.1f}%."
                        ),
                        expected_impact=(
                            "Остановка накопления "
                            "операционных убытков."
                        ),
                        recommended_action=(
                            "Провести cost review, "
                            "пересмотреть pricing "
                            "и определить убыточные "
                            "направления."
                        ),
                    )
                )

            elif margin < 10:

                decisions.append(
                    CFODecision(
                        priority=3,
                        category="profitability",
                        severity="warning",
                        decision=(
                            "Повысить операционную "
                            "маржинальность."
                        ),
                        reason=(
                            f"Net margin составляет "
                            f"{margin:.1f}%."
                        ),
                        expected_impact=(
                            "Рост свободного денежного "
                            "потока."
                        ),
                        recommended_action=(
                            "Оптимизировать расходы "
                            "и проверить pricing."
                        ),
                    )
                )

        # ---------------------------------------------
        # 3. EXTERNAL RISKS
        # ---------------------------------------------

        for impact in external_impacts:

            severity = impact.get(
                "severity",
                "moderate",
            )

            if severity not in {
                "critical",
                "warning",
            }:
                continue

            weight = self.SEVERITY_WEIGHT.get(
                severity,
                0,
            )

            category = impact.get(
                "impact_area",
                "external",
            )

            metric = impact.get(
                "metric",
                "external_factor",
            )

            explanation = impact.get(
                "explanation",
                "",
            )

            action = impact.get(
                "recommended_action",
                "",
            )

            decisions.append(
                CFODecision(
                    priority=weight,
                    category=category,
                    severity=severity,
                    decision=(
                        f"Учитывать влияние "
                        f"{metric} в финансовом "
                        f"планировании."
                    ),
                    reason=explanation,
                    expected_impact=(
                        "Снижение чувствительности "
                        "финансового результата "
                        "к внешнему фактору."
                    ),
                    recommended_action=action,
                )
            )

        # ---------------------------------------------
        # 4. SORT
        # ---------------------------------------------

        decisions.sort(
            key=lambda item: (
                -self.SEVERITY_WEIGHT.get(
                    item.severity,
                    0,
                ),
                item.priority,
            )
        )

        # ---------------------------------------------
        # 5. NORMALIZE PRIORITIES
        # ---------------------------------------------

        normalized: list[CFODecision] = []

        for index, decision in enumerate(
            decisions,
            start=1,
        ):

            normalized.append(
                CFODecision(
                    priority=index,
                    category=decision.category,
                    severity=decision.severity,
                    decision=decision.decision,
                    reason=decision.reason,
                    expected_impact=decision.expected_impact,
                    recommended_action=(
                        decision.recommended_action
                    ),
                )
            )

        return normalized
