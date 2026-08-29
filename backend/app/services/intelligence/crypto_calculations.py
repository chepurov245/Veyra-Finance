from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True)
class CryptoCalculationResult:
    metric: str
    value: float
    unit: str | None = None
    metadata: dict | None = None


class CryptoCalculationEngine:

    @staticmethod
    def pnl(
        entry_value: float,
        exit_value: float,
        fees: float = 0.0,
    ) -> CryptoCalculationResult:
        if entry_value <= 0:
            raise ValueError(
                "Entry value must be greater than zero."
            )

        profit = exit_value - entry_value - fees
        roi = (profit / entry_value) * 100

        return CryptoCalculationResult(
            metric="pnl",
            value=profit,
            unit="currency",
            metadata={
                "roi_percent": roi,
                "fees": fees,
            },
        )

    @staticmethod
    def sharpe_ratio(
        returns: list[float],
        risk_free_rate: float = 0.0,
        periods_per_year: int = 365,
    ) -> CryptoCalculationResult:
        if len(returns) < 2:
            raise ValueError(
                "At least two returns are required."
            )

        excess_returns = [
            value - risk_free_rate
            for value in returns
        ]

        mean = sum(excess_returns) / len(
            excess_returns
        )

        variance = sum(
            (value - mean) ** 2
            for value in excess_returns
        ) / (len(excess_returns) - 1)

        std_dev = sqrt(variance)

        if std_dev == 0:
            raise ValueError(
                "Standard deviation cannot be zero."
            )

        value = (
            mean
            / std_dev
            * sqrt(periods_per_year)
        )

        return CryptoCalculationResult(
            metric="sharpe_ratio",
            value=value,
            metadata={
                "periods_per_year": periods_per_year,
            },
        )

    @staticmethod
    def sortino_ratio(
        returns: list[float],
        target_return: float = 0.0,
        periods_per_year: int = 365,
    ) -> CryptoCalculationResult:
        if len(returns) < 2:
            raise ValueError(
                "At least two returns are required."
            )

        excess_returns = [
            value - target_return
            for value in returns
        ]

        mean = sum(excess_returns) / len(
            excess_returns
        )

        downside = [
            min(value, 0.0)
            for value in excess_returns
        ]

        downside_variance = sum(
            value ** 2
            for value in downside
        ) / len(downside)

        downside_deviation = sqrt(
            downside_variance
        )

        if downside_deviation == 0:
            raise ValueError(
                "Downside deviation cannot be zero."
            )

        value = (
            mean
            / downside_deviation
            * sqrt(periods_per_year)
        )

        return CryptoCalculationResult(
            metric="sortino_ratio",
            value=value,
            metadata={
                "periods_per_year": periods_per_year,
            },
        )

    @staticmethod
    def impermanent_loss(
        price_ratio: float,
    ) -> CryptoCalculationResult:
        if price_ratio <= 0:
            raise ValueError(
                "Price ratio must be greater than zero."
            )

        sqrt_ratio = sqrt(price_ratio)

        lp_value_ratio = (
            2 * sqrt_ratio
            / (1 + price_ratio)
        )

        il = (
            lp_value_ratio - 1
        ) * 100

        return CryptoCalculationResult(
            metric="impermanent_loss",
            value=il,
            unit="%",
            metadata={
                "price_ratio": price_ratio,
                "lp_value_ratio": lp_value_ratio,
            },
        )
