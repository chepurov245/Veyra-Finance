from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalImpact:
    metric: str
    value: float | None
    unit: str | None
    period: str | None
    direction: str
    severity: str
    impact_area: str
    explanation: str
    recommended_action: str


class ExternalImpactEngine:

    def analyze(
        self,
        economic_facts: list[dict],
        derived_metrics: dict[str, float],
    ) -> list[ExternalImpact]:

        impacts: list[ExternalImpact] = []

        for fact in economic_facts:

            metric = (
                fact.get("metric")
                or fact.get("indicator")
            )

            value = fact.get("value")

            if not metric:
                continue

            try:
                numeric_value = (
                    float(value)
                    if value is not None
                    else None
                )
            except (TypeError, ValueError):
                numeric_value = None

            unit = fact.get("unit")
            period = fact.get("period")

            normalized = metric.lower()

            # -----------------------------------------
            # INFLATION
            # -----------------------------------------

            if normalized in {
                "inflation",
                "cpi",
                "consumer_price_index",
            }:

                if numeric_value is None:
                    continue

                if numeric_value >= 5:
                    severity = "critical"
                    direction = "negative"

                elif numeric_value >= 3:
                    severity = "warning"
                    direction = "negative"

                else:
                    severity = "moderate"
                    direction = "neutral"

                impacts.append(
                    ExternalImpact(
                        metric="inflation",
                        value=numeric_value,
                        unit=unit,
                        period=period,
                        direction=direction,
                        severity=severity,
                        impact_area="operating_costs",
                        explanation=(
                            "Повышенная инфляция может "
                            "увеличивать операционные "
                            "расходы компании и создавать "
                            "давление на маржу."
                        ),
                        recommended_action=(
                            "Контролировать рост "
                            "операционных расходов и "
                            "пересматривать цены при "
                            "необходимости."
                        ),
                    )
                )

            # -----------------------------------------
            # INTEREST RATE
            # -----------------------------------------

            elif normalized in {
                "interest_rate",
                "policy_rate",
                "ecb_rate",
                "key_rate",
            }:

                if numeric_value is None:
                    continue

                if numeric_value >= 7:
                    severity = "critical"
                elif numeric_value >= 4:
                    severity = "warning"
                else:
                    severity = "moderate"

                impacts.append(
                    ExternalImpact(
                        metric="interest_rate",
                        value=numeric_value,
                        unit=unit,
                        period=period,
                        direction="negative",
                        severity=severity,
                        impact_area="cost_of_capital",
                        explanation=(
                            "Высокая процентная ставка "
                            "увеличивает стоимость "
                            "финансирования и может "
                            "снижать инвестиционную "
                            "активность."
                        ),
                        recommended_action=(
                            "Оценить стоимость капитала, "
                            "долговую нагрузку и "
                            "необходимость нового "
                            "финансирования."
                        ),
                    )
                )

            # -----------------------------------------
            # GDP
            # -----------------------------------------

            elif normalized in {
                "gdp",
                "gdp_growth",
                "economic_growth",
            }:

                if numeric_value is None:
                    continue

                if numeric_value < -2:
                    severity = "critical"
                    direction = "negative"

                elif numeric_value < 0:
                    severity = "warning"
                    direction = "negative"

                elif numeric_value < 2:
                    severity = "moderate"
                    direction = "neutral"

                else:
                    severity = "healthy"
                    direction = "positive"

                impacts.append(
                    ExternalImpact(
                        metric="gdp",
                        value=numeric_value,
                        unit=unit,
                        period=period,
                        direction=direction,
                        severity=severity,
                        impact_area="demand",
                        explanation=(
                            "Динамика ВВП является "
                            "индикатором состояния "
                            "экономического спроса "
                            "и деловой активности."
                        ),
                        recommended_action=(
                            "Учитывать макроэкономический "
                            "цикл при планировании "
                            "выручки и расходов."
                        ),
                    )
                )

            # -----------------------------------------
            # FX
            # -----------------------------------------

            elif normalized in {
                "exchange_rate",
                "fx",
                "eur_usd",
                "usd_eur",
                "currency_rate",
            }:

                if numeric_value is None:
                    continue

                impacts.append(
                    ExternalImpact(
                        metric="exchange_rate",
                        value=numeric_value,
                        unit=unit,
                        period=period,
                        direction="neutral",
                        severity="moderate",
                        impact_area="currency_risk",
                        explanation=(
                            "Изменение валютного курса "
                            "может влиять на стоимость "
                            "операций, активов и обязательств "
                            "компании в иностранной валюте."
                        ),
                        recommended_action=(
                            "Оценить валютную экспозицию "
                            "компании и влияние изменения "
                            "курса на денежные потоки."
                        ),
                    )
                )

        return impacts
