from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class CalculationResult:
    metric: str
    value: float
    unit: str | None = None
    metadata: dict | None = None


class CalculationEngine:

    @staticmethod
    def percentage_change(
        old_value: float,
        new_value: float,
    ) -> CalculationResult:
        if old_value == 0:
            raise ValueError(
                "Cannot calculate percentage change from zero."
            )

        value = (
            (new_value - old_value)
            / abs(old_value)
        ) * 100

        return CalculationResult(
            metric="percentage_change",
            value=value,
            unit="%",
        )

    @staticmethod
    def roi(
        investment: float,
        final_value: float,
    ) -> CalculationResult:
        if investment == 0:
            raise ValueError(
                "Investment cannot be zero."
            )

        value = (
            (final_value - investment)
            / abs(investment)
        ) * 100

        return CalculationResult(
            metric="roi",
            value=value,
            unit="%",
        )

    @staticmethod
    def cagr(
        initial_value: float,
        final_value: float,
        years: float,
    ) -> CalculationResult:
        if initial_value <= 0:
            raise ValueError(
                "Initial value must be greater than zero."
            )

        if final_value < 0:
            raise ValueError(
                "Final value cannot be negative."
            )

        if years <= 0:
            raise ValueError(
                "Years must be greater than zero."
            )

        value = (
            (final_value / initial_value)
            ** (1 / years)
            - 1
        ) * 100

        return CalculationResult(
            metric="cagr",
            value=value,
            unit="%",
        )

    @staticmethod
    def volatility(
        returns: list[float],
        annualization_factor: float = 252,
    ) -> CalculationResult:
        if len(returns) < 2:
            raise ValueError(
                "At least two returns are required."
            )

        mean = sum(returns) / len(returns)

        variance = sum(
            (value - mean) ** 2
            for value in returns
        ) / (len(returns) - 1)

        value = sqrt(
            variance * annualization_factor
        ) * 100

        return CalculationResult(
            metric="annualized_volatility",
            value=value,
            unit="%",
        )

    @staticmethod
    def max_drawdown(
        values: list[float],
    ) -> CalculationResult:
        if not values:
            raise ValueError(
                "Values cannot be empty."
            )

        peak = values[0]
        max_drawdown = 0.0

        for value in values:
            if value > peak:
                peak = value

            if peak == 0:
                continue

            drawdown = (
                (value - peak)
                / peak
            )

            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return CalculationResult(
            metric="max_drawdown",
            value=max_drawdown * 100,
            unit="%",
        )
